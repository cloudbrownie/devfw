import pygame

from typing import Any

try:
  from .spatialhash import Chunk, SpatialHashMap
  from .elems       import Element
  from .utils       import point2d
except:
  from scripts.devfw.spatialhash  import Chunk, SpatialHashMap
  from elems                      import Element
  from utils                      import point2d

class TexChunk(Chunk):
  'chunk element used for storing tile textures'

  def __init__(self, chunk_pos:point2d, chunk_width:int, tile_size:int):
    super().__init__(None, chunk_pos=chunk_pos, chunk_width=chunk_width, tile_size=tile_size)
    self.textures     : list            = []
    self.cached_surf  : pygame.Surface  = None
    self.surf_buffer  : int             = 2

  def get_textures(self) -> list:
    'returns list of (point2d, (sheet id, texture row, texture col)) of entire chunk'
    self.textures = []    
    for row in range(self.chunk_width):
      for col in range(self.chunk_width):
        if self.grid[row][col] == None:
          continue
        self.textures.append((point2d(col * self.tile_size, row * self.tile_size), self.grid[row][col]))

    return self.textures    
  
  def get_chunk_texture(self) -> pygame.Surface:
    'returns the rendered chunk surface'
    if self.outdated:
      self.cached_surf = pygame.Surface((self.chunk_size + self.surf_buffer, self.chunk_size + self.surf_buffer))
      self.cached_surf.set_colorkey((0, 0, 0))

      for (pos, (sheet_id, tex_row, tex_col)) in self.get_textures():
        texture = self.elements['Sheets'].get_texture(sheet_id, tex_row, tex_col)
        self.cached_surf.blit(texture, (pos.x + self.surf_buffer, pos.y + self.surf_buffer))

      self.outdated = False

    return self.cached_surf
  
  def update_tile_texture(self, row:int, col:int, new_bitmask:int=-1, new_variant:int=-1) -> Any:
    'updates the tile texture info at row, col'
    sheet_id, old_row, old_col = self.get_item(row, col)

    new_row = new_bitmask if new_bitmask != -1 else old_row
    new_col = new_variant if new_variant != -1 else old_col

    return self.swap_item(row, col, (sheet_id, new_row, new_col))

class TexSHMap(SpatialHashMap):
  'spatial hash structure for storing texture chunks'

  def __init__(self, chunk_width:int=16, tile_size:int=16):
    super().__init__(TexChunk, chunk_width=chunk_width, tile_size=tile_size)

  def add_tile(self, worldx:float, worldy:float, sheet_id:int, tex_row:int, tex_col:int, ) -> None:
    'adds the texture data to the world at worldx, worldy'
    super().add_tile(worldx, worldy, (sheet_id, tex_row, tex_col))
  
  def get_terrain(self, query:pygame.Rect, pad:bool=True) -> list[Any]:
    'returns list of pygame.Surfaces representing the map in the query region'
    tags = self.get_chunks_in_rect(query, pad)
    
    textures = []
    for tag in tags:
      chunk_pos = self.chunks[tag].chunk_pos.copy()
      chunk_pos.x *= self.CHUNK_SIZE
      chunk_pos.y *= self.CHUNK_SIZE
      textures.append((chunk_pos, self.chunks[tag].get_chunk_texture()))

    return textures
  
  def update_tile_texture(self, worldx:float, worldy:float, new_bitmask:int=-1, new_variant:int=-1) -> Any:
    'updates the tile texture info at row, col'
    chunk_tag = self.get_chunk_tag(worldx, worldy)
    col, row = self.get_chunk_grid_pos(worldx, worldy)
    return self.chunks[chunk_tag].update_tile_texture(row, col, new_bitmask, new_variant)
  
class TextureMap(Element):
  'map of multiple texture spatial hash structures for texture layering. contains a background, middleground, and foreground layer.'

  def __init__(self, chunk_width:int=16, tile_size:int=16):
    super().__init__()

    self._current_editing_layer : int = 1

    self._texture_layers     : list                = ['-1', '0', '1']
    self._texture_layer_maps : dict[str, TexSHMap] = {}

    for layer in self._texture_layers:
      self._texture_layer_maps[layer] = TexSHMap(chunk_width, tile_size)

  @property
  def layer(self) -> str:
    'current editing layer'
    if self._current_editing_layer == 0:
      return 'background'
    if self._current_editing_layer == 1:
      return 'middleground'
    return 'foreground'
  
  @property
  def editing_layer(self) -> str:
    'current editing layer as stored'
    return self._texture_layers[self._current_editing_layer]

  def increment_editing_layer(self) -> None:
    'increment the current editing layer'
    if self._current_editing_layer < 2:
      self._current_editing_layer += 1

  def decrement_editing_layer(self) -> None:
    'decrement the current editing layer'
    if self._current_editing_layer > 0:
      self._current_editing_layer -= 1

  def add_tile(self, worldx:float, worldy:float, sheet_id:int, tex_row:int, tex_col:int) -> None:
    'adds the texture data to the world at worldx, worldy in the current editing layer'
    self._texture_layer_maps[self.editing_layer].add_tile(worldx, worldy, sheet_id, tex_row, tex_col)

  def del_tile(self, worldx:float, worldy:float) -> Any:
    'deletes the texture data from the world at worldx, worldy in the current editing layer'
    return self._texture_layer_maps[self.editing_layer].del_tile(worldx, worldy)

  def check_tile(self, worldx:float, worldy:float) -> bool:
    'returns boolean if texture data exists at worldx, worldy'
    return self._texture_layer_maps[self.editing_layer].check_tile(worldx, worldy)

  def update_tile_texture(self, worldx:float, worldy:float, bitmask:int, variant:int) -> Any:
    'updates the tile texture info in the world at worldx, worldy in the current editing layer'
    return self._texture_layer_maps[self.editing_layer].update_tile_texture(worldx, worldy, bitmask, variant)

  def get_map(self, query:pygame.Rect) -> list[point2d, pygame.Surface]:
    'returns list of pygame.Surfaces representing the map in the query region, ordered by layer'
    textures = []
    for layer in self._texture_layers:
      textures.extend(self._texture_layer_maps[layer].get_terrain(query))

    return textures