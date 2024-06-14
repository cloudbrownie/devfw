import pygame
import pickle
import gzip
import zlib

try:
  from .elems import Singleton
  from .utils import point2d
except:
  from elems import Singleton
  from utils import point2d

class Chunk:
  'used for storing chunk data in tilemap\'s spatial hash structure'
  def __init__(self, chunk_pos:point2d, chunk_width:int, tile_size:int):
    self.chunk_pos : point2d = chunk_pos
    self.chunk_width : int = chunk_width
    self.chunk_size : int = chunk_width * tile_size
    self.tile_size : int = tile_size
    self.grid : list[list[int]] = [[0 for _ in range(chunk_width)] for _ in range(chunk_width)]
    self.count : int = 0
    self.collidables : list = []
    self.outdated : bool = False

  def from_bitstring(self, bitstring:str, optimize:bool=True) -> None:
    self.count = 0
    self.collidables = []

    row = 0
    col = 0
    for i in range(len(bitstring)):
      if i % self.tile_size == 0 and i > 0:
        row += 1
        col = 0
      self.grid[row][col] = int(bitstring[i])
      col += 1

    if optimize:
      self.optimize()

  def add_tile(self, row:int, col:int) -> None:
    'sets the row, col to be collidable'
    if self.grid[row][col] != 1:
      self.count += 1
      self.outdated = True
    self.grid[row][col] = 1

  def check_tile(self, row:int, col:int) -> bool:
    'returns whether a tile exists in this location'
    return self.grid[row][col] == 1

  def del_tile(self, row:int, col:int) -> None:
    'set the row, col to not be collidable'
    if self.grid[row][col] != 0:
      self.count -= 1
      self.outdated = True
    self.grid[row][col] = 0

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

class Tilemap(Singleton):
  def __init__(self, chunk_width:int=16, tile_size:int=16):
    super().__init__()

    self.chunks : dict[str, Chunk] = {}
    self.CHUNK_WIDTH : int = chunk_width
    self.TILE_SIZE : int = tile_size

  @property
  def CHUNK_SIZE(self) -> int:
    'returns the integer size of the chunk'
    return self.CHUNK_WIDTH * self.TILE_SIZE

  def get_chunk_pos(self, worldx:float, worldy:float) -> tuple[int, int]:
    'returns chunk pos as x, y in chunk scale using world coords'
    return int(worldx // self.CHUNK_SIZE), int(worldy // self.CHUNK_SIZE)

  def get_chunk_tag(self, worldx:float, worldy:float) -> str:
    'returns the chunk tag using world coords'
    return self._format_chunk_tag(*self.get_chunk_pos(worldx, worldy))

  def _format_chunk_tag(self, chunkx:int, chunky:int) -> str:
    'formats the chunkx and chunky into a chunk tag'
    return f'{chunkx},{chunky}'

  def _unformat_chunk_tag(self, tag:str) -> tuple[int, int]:
    'returns the chunkx and chunky from a chunk tag'
    x, y = tag.split(',')
    return int(x), int(y)

  def get_world_grid_pos(self, worldx:float, worldy:float) -> tuple[int, int]:
    'returns col, row of world coordinates in tile scale'
    return int(worldx // self.TILE_SIZE), int(worldy // self.TILE_SIZE)

  def get_chunk_grid_pos(self, worldx:float, worldy:float) -> tuple[int, int]:
    'returns col, row of world coordinates in tile scale and modulo\'d by chunk width'
    world_grid_x, world_grid_y = self.get_world_grid_pos(worldx, worldy)
    return world_grid_x % self.CHUNK_WIDTH, world_grid_y % self.CHUNK_WIDTH

  def add_tile(self, worldx:float, worldy:float) -> None:
    'sets this world tile position as a collidable tile'
    chunkx, chunky = self.get_chunk_pos(worldx, worldy)
    chunk_tag = self._format_chunk_tag(chunkx, chunky)

    if chunk_tag not in self.chunks:
      self.chunks[chunk_tag] = Chunk(
        point2d(chunkx, chunky),
        self.CHUNK_WIDTH,
        self.TILE_SIZE
      )

    col, row = self.get_chunk_grid_pos(worldx, worldy)
    self.chunks[chunk_tag].add_tile(row, col)
    self.chunks[chunk_tag].optimize()

  def remove_tile(self, worldx:float, worldy:float, del_empty:bool=True) -> None:
    'removes this world tile position from being collidable, deletes the chunk if chunk then becomes empty'
    chunkx, chunky = self.get_chunk_pos(worldx, worldy)
    chunk_tag = self._format_chunk_tag(chunkx, chunky)

    if chunk_tag not in self.chunks:
      return

    col, row = self.get_chunk_grid_pos(worldx, worldy)
    self.chunks[chunk_tag].del_tile(row, col)

    if del_empty and self.chunks[chunk_tag].count == 0:
      del self.chunks[chunk_tag]

    else:
      self.chunks[chunk_tag].optimize()

  def get_tile(self, worldx:float, worldy:float) -> pygame.Rect:
    'returns the rect of a tile that collides with worldx, worldy, otherwise returns none'
    chunkx, chunky = self.get_chunk_pos(worldx, worldy)
    chunk_tag = self._format_chunk_tag(chunkx, chunky)

    if chunk_tag not in self.chunks:
      return None

    col, row = self.get_chunk_grid_pos(worldx, worldy)

    if not self.chunks[chunk_tag].check_tile(row, col):
      return None

    rx = col * self.TILE_SIZE + chunkx * self.CHUNK_SIZE
    ry = row * self.TILE_SIZE + chunky * self.CHUNK_SIZE

    return pygame.Rect(rx, ry, self.TILE_SIZE, self.TILE_SIZE)

  def get_chunks_in_rect(self, query:pygame.Rect, pad:bool=True) -> list[str]:
    'returns the chunk tags of all chunks within query rect'
    x_start  = query.x // self.CHUNK_SIZE
    y_start  = query.y // self.CHUNK_SIZE
    x_chunks = query.w // self.CHUNK_SIZE
    y_chunks = query.h // self.CHUNK_SIZE

    if pad:
      x_start -= 1
      y_start -= 1
      x_chunks += 3
      y_chunks += 3

    x_chunk_range = range(x_start, x_start + x_chunks, 1)
    y_chunk_range = range(y_start, y_start + y_chunks, 1)

    chunks = []

    for chunk_x in x_chunk_range:
      for chunk_y in y_chunk_range:
        chunk_tag = f'{chunk_x},{chunk_y}'
        if chunk_tag not in self.chunks:
          continue

        chunks.append(chunk_tag)

    return chunks

  def get_terrain(self, query:pygame.Rect, pad:bool=True) -> list[pygame.Rect]:
    'returns list of pygame.Rect\'s representing collidable terrain'
    tags = self.get_chunks_in_rect(query, pad)

    terrain = []
    for tag in tags:
      terrain.extend(self.chunks[tag].get_collidables())

    return terrain

  def save(self, path:str) -> None:

    chunk_data = {}

    for chunk_pos in self.chunks:

      chunk = self.chunks[chunk_pos]

      bitstring = ''

      for row in chunk.grid:
        for col in row:
          bitstring += str(col)

      chunk_data[chunk_pos] = bitstring

    data = {
      'width':self.CHUNK_WIDTH,
      'size':self.TILE_SIZE,
      'data':chunk_data
    }

    with gzip.open(path, 'wb') as f:
      f.write(zlib.compress(pickle.dumps(data)))

  def load(self, path:str) -> None:
    with gzip.open(path, 'rb') as f:
      data = pickle.loads(zlib.decompress(f.read()))

      chunk_data  = data['data']
      chunk_width = data['width']
      tile_size   = data['size']

      self.chunks.clear()

      for chunk_hash in chunk_data:

        chunk_pos = point2d(*self._unformat_chunk_tag(chunk_hash))
        self.chunks[chunk_hash] = Chunk(chunk_pos, chunk_width, tile_size)

        self.chunks[chunk_hash].from_bitstring(chunk_data[chunk_hash])

