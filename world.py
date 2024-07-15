import pygame
import pickle
import gzip
import zlib

try:
  from .tilemap     import TileSHMap
  from .decormap    import DecorSHMap
  from .texmap      import TexSHMap
  from .spatialhash import LayeredSHMap
  from .elems       import Element
except:
  from tilemap      import TileSHMap
  from decormap     import DecorSHMap
  from texmap       import TexSHMap
  from spatialhash  import LayeredSHMap
  from elems        import Element


class World(Element):
  def __init__(self, chunk_width:int=16, tile_size:int=16):
    super().__init__()

    self._tile_map    : TileSHMap     = TileSHMap(chunk_width, tile_size)
    self._texture_map : LayeredSHMap  = LayeredSHMap(TexSHMap, chunk_width, tile_size)
    self._decor_map   : LayeredSHMap  = LayeredSHMap(DecorSHMap, chunk_width, tile_size)

  @property
  def texture_layer(self) -> str:
    return self._texture_map.layer

  # tilemap operations ---------------------------------------------------------

  def add_tile(self, worldx:float, worldy:float) -> None:
    self._tile_map.add_tile(worldx, worldy)

  def del_tile(self, worldx:float, worldy:float):
    self._tile_map.del_tile(worldx, worldy)

  def get_terrain(self, query:pygame.Rect) -> list:
    return self._tile_map.get_terrain(query)
  
  def get_grid_positions(self, query:pygame.Rect) -> list:
    return self._tile_map.get_grid_positions(query)

  # texturemap operations -----------------------------------------------------

  def add_texture(self, worldx:float, worldy:float, sheet_id:int, tex_row:int, tex_col:int) -> None:
    self._texture_map.add_tile(worldx, worldy, sheet_id, tex_row, tex_col)

  def del_texture(self, worldx:float, worldy:float):
    self._texture_map.del_tile(worldx, worldy)

  def check_texture(self, worldx:float, worldy:float) -> bool:
    return self._texture_map.check_tile(worldx, worldy)

  def update_texture(self, worldx:float, worldy:float, bitmask:int, variant:int):
    self._texture_map.update_tile_texture(worldx, worldy, bitmask, variant)

  def increment_texture_layer(self):
    self._texture_map.increment_editing_layer()

  def decrement_texture_layer(self):
    self._texture_map.decrement_editing_layer()

  # decormap operations --------------------------------------------------------

  def add_decor(self, worldx:float, worldy:float, sheet_id:int, tex_row:int, tex_col:int) -> None:
    self._decor_map.add_tile(worldx, worldy, sheet_id, tex_row, tex_col)

  def del_decor(self, worldx:float, worldy:float):
    self._decor_map.del_tile(worldx, worldy)

  # world operations -----------------------------------------------------------

  def get_map(self, query:pygame.Rect):
    texture_layers = self._texture_map.get_map(query)
    decor_layers = self._decor_map.get_map(query)

    ordered_map = []
    for i in range(3):
      ordered_map.extend(texture_layers[i])
      ordered_map.extend(decor_layers[i])

    return ordered_map
  
  def save_map(self, path:str):
    tile_data = self._tile_map.get_save_data()
    texture_data = self._texture_map.get_save_data()
    decor_data = self._decor_map.get_save_data()

    data = {
      'tile':tile_data,
      'texture':texture_data,
      'decor':decor_data
    }

    print(data)
    import sys

    pickle_size = sys.getsizeof(pickle.dumps(tile_data))
    pickle_size += sys.getsizeof(pickle.dumps(texture_data))
    pickle_size += sys.getsizeof(pickle.dumps(decor_data))

    print(f'COMPRESSED SIZE: {sys.getsizeof(zlib.compress(pickle.dumps(data)))}')
    print(f'SERIALIZED SIZE: {pickle_size}')

    with gzip.open(path, 'wb') as f:
      f.write(zlib.compress(pickle.dumps(data)))

  def load_map(self, path:str):

    with gzip.open(path, 'rb') as f:
      data = pickle.loads(zlib.decompress(f.read()))

      print(data)

      self._tile_map.load_from_data(data['tile'])
      self._texture_map.load_from_data(data['texture'])
      self._decor_map.load_from_data(data['decor'])