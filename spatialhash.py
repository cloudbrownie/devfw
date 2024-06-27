import pygame
import pickle
import gzip
import zlib

from typing import Any

try:
  from .elems import Element
  from .utils import point2d
except:
  from elems import Element
  from utils import point2d


class Chunk(Element):
  'used for storing data in chunks for spatial hash'

  def __init__(self, default:Any, chunk_pos:point2d, chunk_width:int, tile_size:int):
    super().__init__()
    self.chunk_pos   : point2d = chunk_pos
    self.chunk_width : int = chunk_width
    self.chunk_size  : int = chunk_width * tile_size
    self.tile_size   : int = tile_size
    self.default     : Any = default
    self.grid        : list[list[Any]] = [[default for _ in range(chunk_width)] for _ in range(chunk_width)]
    self.count       : int = 0
    self.outdated    : bool = True

  def add_item(self, row:int, col:int, data:Any) -> None:
    'add item to chunk at <row>, <col>'
    if self.grid[row][col] == None:
      self.count += 1
    self.grid[row][col] = data
    self.outdated = True

  def del_item(self, row:int, col:int) -> Any:
    'returns item in chunk at <row>, <col> and deletes it'
    if self.grid[row][col] != None:
      self.count -= 1
    item = self.grid[row][col]
    self.grid[row][col] = self.default
    self.outdated = True
    return item

  def get_item(self, row:int, col:int) -> Any:
    'returns item in chunk at <row>, <col>'
    return self.grid[row][col]

  def check_item(self, row:int, col:int) -> bool:
    'returns boolean of item status at <row>, <col>'
    return self.get_item(row, col) != self.default

  def swap_item(self, row:int, col:int, data:Any) -> Any:
    'returns item in chunk at <row>, <col> and replaces with new item'
    item = self.grid[row][col]
    self.grid[row][col] = data
    return item

  def get_save_data(self) -> Any:
    'returns a saveable object with enough data to reconstruct this chunk'
    return None

  def reconstruct(self, data:Any) -> None:
    'reconstructs chunk with given save data'

class SpatialHashMap(Element):
  'generic spatial hash implementation'

  def __init__(self, chunk_type:Any=Chunk, chunk_width:int=16, tile_size:int=16):
    super().__init__()

    self.chunk_type  : Any = chunk_type

    self.chunks      : dict[str, self.chunk_type] = {}
    self.CHUNK_WIDTH : int = chunk_width
    self.TILE_SIZE   : int = tile_size

  @property
  def CHUNK_SIZE(self) -> int:
    'returns integer size of the chunk'
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

  def add_tile(self, worldx:float, worldy:float, data:Any) -> None:
    'add tile data to this world tile position'
    chunkx, chunky = self.get_chunk_pos(worldx, worldy)
    chunk_tag = self._format_chunk_tag(chunkx, chunky)

    if chunk_tag not in self.chunks:
      self.chunks[chunk_tag] = self.chunk_type(
        point2d(chunkx, chunky),
        self.CHUNK_WIDTH,
        self.TILE_SIZE
      )

    col, row = self.get_chunk_grid_pos(worldx, worldy)
    self.chunks[chunk_tag].add_item(row, col, data)

  def del_tile(self, worldx:float, worldy:float, del_empty:bool=True) -> None:
    'removes data from this world tile position, deletes the chunk if chunk then becomes empty'
    chunkx, chunky = self.get_chunk_pos(worldx, worldy)
    chunk_tag = self._format_chunk_tag(chunkx, chunky)

    if chunk_tag not in self.chunks:
      return

    col, row = self.get_chunk_grid_pos(worldx, worldy)
    self.chunks[chunk_tag].del_item(row, col)

    if del_empty and self.chunks[chunk_tag].count == 0:
      del self.chunks[chunk_tag]

  def get_tile(self, worldx:float, worldy:float) -> pygame.Rect:
    'returns data of a tile that collides with worldx, worldy, otherwise returns none'
    chunkx, chunky = self.get_chunk_pos(worldx, worldy)
    chunk_tag = self._format_chunk_tag(chunkx, chunky)

    if chunk_tag not in self.chunks:
      return None

    col, row = self.get_chunk_grid_pos(worldx, worldy)

    if not self.chunks[chunk_tag].check_item(row, col):
      return None

    return self.chunks[chunk_tag].get_item(row, col)
  
  def check_tile(self, worldx:float, worldy:float) -> bool:
    'returns boolean if tile exists at worldx, worldy'
    chunkx, chunky = self.get_chunk_pos(worldx, worldy)
    chunk_tag = self._format_chunk_tag(chunkx, chunky)

    if chunk_tag not in self.chunks:
      return False
    
    col, row = self.get_chunk_grid_pos(worldx, worldy)
    return self.chunks[chunk_tag].check_item(row, col)

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

  def save(self, path:str) -> None:
    'base save method for the spatial hash tree to a json'

    chunk_data = {}

    for chunk_pos in self.chunks:
      chunk_data[chunk_pos] = self.chunks[chunk_pos].get_save_data()

    data = {
      'width':self.CHUNK_WIDTH,
      'size':self.TILE_SIZE,
      'data':chunk_data
    }

    with gzip.open(path, 'wb') as f:
      f.write(zlib.compress(pickle.dumps(data)))


  def load(self, path:str) -> None:
    'base load method for the spatial hash tree to a json'

    with gzip.open(path, 'rb') as f:
      data = pickle.loads(zlib.decompress(f.read()))

      chunk_data  = data['data']
      chunk_width = data['width']
      tile_size   = data['size']

      self.chunks.clear()

      for chunk_hash in chunk_data:

        chunk_pos = point2d(*self._unformat_chunk_tag(chunk_hash))
        self.chunks[chunk_hash] = self.chunk_type(chunk_pos, chunk_width, tile_size)

        self.chunks[chunk_hash].reconstruct(chunk_data[chunk_hash])

