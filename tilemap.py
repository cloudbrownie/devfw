import pygame

from typing import Any

try:
  from .spatialhash import Chunk, SpatialHashMap
  from .utils       import point2d, reshape
except:
  from spatialhash  import Chunk, SpatialHashMap
  from utils        import point2d, reshape

class TileChunk(Chunk):
  'chunk element used for storing collidable tile hitboxes'

  def __init__(self, chunk_pos:point2d, chunk_width:int, tile_size:int):
    super().__init__(0, chunk_pos=chunk_pos, chunk_width=chunk_width, tile_size=tile_size)
    self.collidables : list = []

  def get_collidables(self) -> list:
    'returns list of collidable rects in the chunk'
    # if collidables are outdated, recompute all rects
    if self.outdated:
      self.optimize()

    return self.collidables

  def optimize(self) -> None:
    'greedy meshes the collidables into larger blocks'
    processed = [[False]*self.chunk_width for _ in range(self.chunk_width)]
    boxes = []

    for y in range(self.chunk_width):
      for x in range(self.chunk_width):
        if self.grid[y][x] == 1 and not processed[y][x]:
          # Start a new box
          width = 1
          height = 1

          # Determine the maximum width
          while (x + width < self.chunk_width and all(self.grid[y][x + i] == 1 and not processed[y][x + i] for i in range(width + 1))):
            width += 1

          # Determine the maximum height for this width
          all_good = True
          while (y + height < self.chunk_width and all_good):
            if all(self.grid[y + height][x + i] == 1 and not processed[y + height][x + i] for i in range(width)):
              height += 1
            else:
              all_good = False

          # Mark cells as processed and store the box
          for i in range(height):
            for j in range(width):
              processed[y + i][x + j] = True
          boxes.append((x, y, width, height))

    self.collidables = []
    for (x, y, w, h) in boxes:
      self.collidables.append(
        pygame.Rect(
          x * self.tile_size + self.chunk_pos.x * self.chunk_size,
          y * self.tile_size + self.chunk_pos.y * self.chunk_size,
          w * self.tile_size,
          h * self.tile_size
        )
      )
    self.outdated = False

  def get_save_data(self) -> Any:
    'returns a saveable object with enough data to reconstruct this chunk'
    data_str = ''
    curr = 0
    run = 0

    for i in range(self.chunk_width ** 2):
      row, col = reshape(i, self.chunk_width)
      if self.grid[row][col] != curr:
        data_str += str(run) + '/'
        run = 1
        curr = self.grid[row][col]
      else:
        run += 1
    data_str += str(run)

    return data_str

  def reconstruct(self, data:Any) -> None:
    super().reconstruct()
    self.collidables = []

    runs = [int(run) for run in data.split('/')]
    curr = 0
    i = 0
    for run in runs:
      if curr == 1:
        self.count += run

      for _ in range(run):
        row, col = reshape(i, self.chunk_width)
        self.grid[row][col] = curr
        i += 1
      curr = 1 if curr == 0 else 0

    self.optimize()

class TileSHMap(SpatialHashMap):
  'spatial hash structure for storing collision chunks'

  def __init__(self, chunk_width:int=16, tile_size:int=16):
    super().__init__(TileChunk, chunk_width=chunk_width, tile_size=tile_size)

  def add_tile(self, worldx: float, worldy: float) -> None:
    'adds a collision hitbox to the world at worldx, worldy'
    super().add_tile(worldx, worldy, 1)

  def del_tile(self, worldx:float, worldy:float, del_empty:bool=True) -> None:
    'deletes a collision hitbox from the world at worldx, worldy'
    super().del_tile(worldx, worldy, del_empty=del_empty)

  def get_terrain(self, query:pygame.Rect, pad:bool=True) -> list[pygame.Rect]:
    'returns list of pygame.Rects representing collidable terrain in the query region'
    tags = self.get_chunks_in_rect(query, pad)

    terrain = []
    for tag in tags:
      terrain.extend(self.chunks[tag].get_collidables())

    return terrain
