import pygame
import pprint
import bitarray


try:
  from .elems import Singleton
  from .elems import Element
except:
  from elems  import Singleton
  from elems  import Element

class Tilemap(Singleton):
  def __init__(self, chunk_size:int=16, tile_size:int=16):
    super().__init__()

    self.chunks : dict = {}
    self.CHUNK_WIDTH : int = chunk_size
    self.TILE_SIZE : int = tile_size
    self.layers : set = set()

  @property
  def CHUNK_SIZE(self) -> int:
    return self.CHUNK_WIDTH * self.TILE_SIZE

  # returns chunk pos as x, y in chunk scale using world coords
  def get_chunk_pos(self, worldx:float, worldy:float) -> tuple[int, int]:
    return int(worldx // self.CHUNK_SIZE), int(worldy // self.CHUNK_SIZE)

  # returns the chunk tag using world coords
  def get_chunk_tag(self, worldx:float, worldy:float) -> str:
    cx, cy = self.get_chunk_pos(worldx, worldy)
    return f'{cx},{cy}'

  def _unformat_chunk_tag(self, tag:str) -> tuple[int, int]:
    x, y = tag.split(',')
    return int(x), int(y)

  # return world grid position in tile scale
  def get_world_grid_pos(self, worldx:float, worldy:float) -> tuple[int, int]:
    return int(worldx // self.TILE_SIZE), int(worldy // self.TILE_SIZE)

  def get_chunk_grid_pos(self, worldx:float, worldy:float) -> tuple[int, int]:
    world_grid_x, world_grid_y = self.get_world_grid_pos(worldx, worldy)
    return world_grid_x % self.CHUNK_WIDTH, world_grid_y % self.CHUNK_WIDTH

  def _compress_tile_pos(self, grid_x:int, grid_y:int) -> str:
    return str(grid_y * self.TILE_SIZE + grid_x)

  def _uncompress_tile_pos(self, tile_pos:str) -> tuple[int, int]:
    flattened = int(tile_pos)
    return int(flattened % self.TILE_SIZE), int(flattened / self.TILE_SIZE)

  # adds tile to the system, can also replace tile if it doesn't exist
  def add_tile(self, worldx:float, worldy:float, layer:str, tex:int, tex_bitmask:int=255, variant:int=0, replace:bool=False) -> None:
    chunk_tag = self.get_chunk_tag(worldx, worldy)

    grid_x, grid_y = self.get_chunk_grid_pos(worldx, worldy)
    compressed_pos = self._compress_tile_pos(grid_x, grid_y)
    tex_data = tex, tex_bitmask, variant

    if chunk_tag not in self.chunks:
      self.chunks[chunk_tag] = {}

    # following 2 cases: tile cannot possibly exist already
    if layer not in self.layers:
      self.layers.add(layer)
      self.layers = sorted(self.layers)

      self.chunks[chunk_tag][layer] = {compressed_pos:tex_data}

    elif layer not in self.chunks[chunk_tag]:
      self.chunks[chunk_tag][layer] = {compressed_pos:tex_data}

    # tile exists already and we wanna replace OR tile doesn't exist
    if (compressed_pos in self.chunks[chunk_tag][layer] and replace) or (compressed_pos not in self.chunks[chunk_tag][layer]):
      self.chunks[chunk_tag][layer][compressed_pos] = tex_data

  # removes tile from system and returns texture data
  def remove_tile(self, worldx:float, worldy:float, layer:str) -> tuple[int, int, int]:
    chunk_tag = self.get_chunk_tag(worldx, worldy)

    # chunk or layer don't exist
    if (chunk_tag not in self.chunks) or (layer not in self.chunks[chunk_tag]):
      print(chunk_tag, self.chunks.keys())
      print(layer, self.chunks.get(chunk_tag, {}).keys())
      return None

    grid_x, grid_y = self.get_chunk_grid_pos(worldx, worldy)
    compressed_pos = self._compress_tile_pos(grid_x, grid_y)

    # will remove the tile from the layer of chunk (works if tile doesn't exist), and returns value (defaults None)

    tex_data = self.chunks[chunk_tag][layer].pop(compressed_pos, None)

    # remove empty layers from chunk to clean data
    if len(self.chunks[chunk_tag][layer]) == 0:
      del self.chunks[chunk_tag][layer]

    # now check if chunk should be removed (if no more layers)
    if len(self.chunks[chunk_tag]) == 0:
      del self.chunks[chunk_tag]

    return tex_data

  # returns the tile's texture data using world coordinates
  def get_tile(self, worldx:float, worldy:float, layer:str) -> tuple[int, int, int]:
    chunk_tag = self.get_chunk_tag(worldx, worldy)

    # chunk or layer don't exist
    if (chunk_tag not in self.chunks) or (layer not in self.chunks[chunk_tag]):
      return None

    grid_x, grid_y = self.get_chunk_grid_pos(worldx, worldy)
    compressed_pos = self._compress_tile_pos(grid_x, grid_y)

    return self.chunks[chunk_tag][layer].get(compressed_pos)

  # grabs all tile's world position (uncompressed) and texture data within given rect
  def get_tiles_in_rect(self, rect:pygame.Rect, layer:str, pad:bool=True) -> list[tuple[tuple[int, int], tuple[int, int, int]]]:

    visible_chunks = self.get_visible_chunks(rect, layer, pad)

    tiles = []

    for chunk_tag in visible_chunks:
      if (chunk_tag not in self.chunks) or (layer not in self.chunks[chunk_tag]):
        continue
      chunk_x, chunk_y = self._unformat_chunk_tag(chunk_tag)

      # iterate through all tiles
      for compressed_pos, tex_data in self.chunks[chunk_tag][layer].items():

        # compute tile world pos
        grid_x, grid_y = self._uncompress_tile_pos(compressed_pos)
        tw_x = grid_x * self.TILE_SIZE + chunk_x * self.CHUNK_SIZE
        tw_y = grid_y * self.TILE_SIZE + chunk_y * self.CHUNK_SIZE

        tiles.append(((tw_x, tw_y), tex_data))

    return tiles

  def get_visible_chunks(self, rect:pygame.Rect, layer:str, pad:bool=True) -> list[str]:
    x_start  = rect.x // self.CHUNK_SIZE
    y_start  = rect.y // self.CHUNK_SIZE
    x_chunks = rect.w // self.CHUNK_SIZE
    y_chunks = rect.h // self.CHUNK_SIZE

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
        if (chunk_tag not in self.chunks) or (layer not in self.chunks[chunk_tag]):
          continue

        chunks.append(chunk_tag)

    return chunks

  def get_chunk_as_bitgrid(self, chunk_tag:str, layer:str) -> list[bitarray.bitarray]:
    if (chunk_tag not in self.chunks) or (layer not in self.chunks[chunk_tag]):
      return []

    grid = [bitarray.bitarray(self.CHUNK_WIDTH) for _ in range(self.CHUNK_WIDTH)]

    for i in range(self.CHUNK_WIDTH):
      for j in range(self.CHUNK_WIDTH):
        compressed_pos = self._compress_tile_pos(i, j)
        if compressed_pos in self.chunks[chunk_tag][layer]:
          grid[i][j] = 1

    return grid

  # returns list of greedily meshed rects for the chunk
  def greedy_mesh_chunk(self, chunk_tag:str, layer:str) -> list[pygame.Rect]:
    if (chunk_tag not in self.chunks) or (layer not in self.chunks[chunk_tag]):
      return []

    grid = self.get_chunk_as_bitgrid(chunk_tag, layer)

  def save(self, path:str, compress=True) -> None:

    params = {
      'tile_size':self.TILE_SIZE,
      'chunk_width':self.CHUNK_WIDTH,
      'cmprsd':compress
    }

    if compress:
      chunks = {}
      for chunk_tag in self.chunks:
        chunks[chunk_tag] = {}
        for layer in self.chunks[chunk_tag]:
          chunks[chunk_tag][layer] = []
          for compressed_pos, (tex, bitmask, variant) in self.chunks[chunk_tag][layer].items():
            tex_data = (tex << 16) | (variant << 8) | (bitmask)
            chunks[chunk_tag][layer].append(int(compressed_pos) << 24 | tex_data)

    map_data = {
      'params':params,
      'chunks':chunks,
      'layers':self.layers
    }

    pretty_map_data = pprint.pformat(map_data, width=4096, indent=2)

    with open(path, 'w') as f:
      f.write(pretty_map_data)

  # overwrites current instance variables with loaded values
  def load(self, path:str) -> None:
    data = None
    with open(path, 'r') as f:
      data = eval(f.read())

    params = data['params']

    self.TILE_SIZE   = params['tile_size']
    self.CHUNK_WIDTH = params['chunk_width']

    if params['cmprsd']:
      chunks = {}
      for chunk in data['chunks']:
        chunks[chunk] = {}
        for layer in data['chunks'][chunk]:
          chunks[chunk][layer] = {}
          for tile in data['chunks'][chunk][layer]:
            bitmask = tile & 255
            variant = tile >> 8 & 255
            tex     = tile >> 16 & 255
            pos     = str(tile >> 24)
            chunks[chunk][layer][pos] = tex, bitmask, variant
      self.chunks = chunks

    else:
      self.chunks = data['chunks']
      print(type(self.chunks))

    self.layers = data['layers']