import pygame

from typing import Any

try:
  from .spatialhash import Chunk, SpatialHashMap
  from .utils   import point2d
except:
  from spatialhash import Chunk, SpatialHashMap
  from utils   import point2d

class TileChunk(Chunk):
  def __init__(self, chunk_pos:point2d, chunk_width:int, tile_size:int):
    super().__init__(0, chunk_pos=chunk_pos, chunk_width=chunk_width, tile_size=tile_size)
    self.collidables : list = []

  def get_collidables(self) -> list:
    'returns list of collidable rects in the chunk'
    # if collidables are outdated, recompute all rects
    if self.outdated:
      self.collidables = []
      for row in range(self.chunk_width):
        for col in range(self.chunk_width):
          if self.grid[row][col] == 0:
            continue

          rect = pygame.Rect(
            col * self.tile_size + self.chunk_pos.x * self.chunk_size,
            row * self.tile_size + self.chunk_pos.y * self.chunk_size,
            self.tile_size,
            self.tile_size
          )

          self.collidables.append(rect)
      self.outdated = False

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
    bitstring = ''
    for row in self.grid:
      for col in row:
        bitstring += str(col)

    return bitstring

  def reconstruct(self, data:Any) -> None:
    self.count = 0
    self.collidables = []

    row = 0
    col = 0
    for i in range(len(data)):
      if i % self.tile_size == 0 and i > 0:
        row += 1
        col = 0
      self.grid[row][col] = int(data[i])
      col += 1

    self.optimize()

class TileSHMap(SpatialHashMap):
  def __init__(self, chunk_width:int=16, tile_size:int=16):
    super().__init__(TileChunk, chunk_width=chunk_width, tile_size=tile_size)

  def add_tile(self, worldx: float, worldy: float) -> None:
    super().add_tile(worldx, worldy, 1)
    self.chunks[self.get_chunk_tag(worldx, worldy)].optimize()

  def del_tile(self, worldx:float, worldy:float, del_empty:bool=True) -> None:
    super().del_tile(worldx, worldy, del_empty=del_empty)
    self.chunks[self.get_chunk_tag(worldx, worldy)].optimize()

  def get_terrain(self, query:pygame.Rect, pad:bool=True) -> list[pygame.Rect]:
    'returns list of pygame.Rect\'s representing collidable terrain'
    tags = self.get_chunks_in_rect(query, pad)

    terrain = []
    for tag in tags:
      terrain.extend(self.chunks[tag].get_collidables())

    return terrain

