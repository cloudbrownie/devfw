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
    if self.outdated:
      self.cached_surf = pygame.Surface((self.chunk_size + self.surf_buffer, self.chunk_size + self.surf_buffer))
      self.cached_surf.set_colorkey((0, 0, 0))

      for (pos, (sheet_id, tex_row, tex_col)) in self.get_textures():
        texture = self.elements['Sheets'].get_texture(sheet_id, tex_row, tex_col)
        self.cached_surf.blit(texture, (pos.x + self.surf_buffer, pos.y + self.surf_buffer))

      self.outdated = False

    return self.cached_surf
  
  def update_tile_texture(self, row:int, col:int, new_bitmask:int=-1, new_variant:int=-1) -> Any:
    sheet_id, old_row, old_col = self.get_item(row, col)

    new_row = new_bitmask if new_bitmask != -1 else old_row
    new_col = new_variant if new_variant != -1 else old_col

    return self.swap_item(row, col, (sheet_id, new_row, new_col))

class TexSHMap(SpatialHashMap):
  def __init__(self, chunk_width:int=16, tile_size:int=16):
    super().__init__(TexChunk, chunk_width=chunk_width, tile_size=tile_size)

  def add_tile(self, worldx:float, worldy:float, sheet_id:int, tex_row:int, tex_col:int, ) -> None:
    super().add_tile(worldx, worldy, (sheet_id, tex_row, tex_col))
  
  def get_terrain(self, query:pygame.Rect, pad:bool=True) -> list[Any]:
    tags = self.get_chunks_in_rect(query, pad)
    
    textures = []
    for tag in tags:
      chunk_pos = self.chunks[tag].chunk_pos.copy()
      chunk_pos.x *= self.CHUNK_SIZE
      chunk_pos.y *= self.CHUNK_SIZE
      textures.append((chunk_pos, self.chunks[tag].get_chunk_texture()))

    return textures
  
  def update_tile_texture(self, worldx:float, worldy:float, new_bitmask:int=-1, new_variant:int=-1) -> Any:
    chunk_tag = self.get_chunk_tag(worldx, worldy)
    col, row = self.get_chunk_grid_pos(worldx, worldy)
    return self.chunks[chunk_tag].update_tile_texture(row, col, new_bitmask, new_variant)
  
class TextureMap(Element):
  def __init__(self, chunk_width:int=16, tile_size:int=16):
    super().__init__()

    self._current_editing_layer : int = 1

    self._texture_layers     : list                = ['-1', '0', '1']
    self._texture_layer_maps : dict[str, TexSHMap] = {}

    for layer in self._texture_layers:
      self._texture_layer_maps[layer] = TexSHMap(chunk_width, tile_size)

  @property
  def layer(self) -> str:
    if self._current_editing_layer == 0:
      return 'background'
    if self._current_editing_layer == 1:
      return 'middleground'
    return 'foreground'
  
  @property
  def editing_layer(self) -> str:
    return self._texture_layers[self._current_editing_layer]

  def increment_editing_layer(self) -> None:
    if self._current_editing_layer < 2:
      self._current_editing_layer += 1

  def decrement_editing_layer(self) -> None:
    if self._current_editing_layer > 0:
      self._current_editing_layer -= 1

  def add_tile(self, worldx:float, worldy:float, sheet_id:int, tex_row:int, tex_col:int) -> None:
    self._texture_layer_maps[self.editing_layer].add_tile(worldx, worldy, sheet_id, tex_row, tex_col)

  def del_tile(self, worldx:float, worldy:float) -> Any:
    return self._texture_layer_maps[self.editing_layer].del_tile(worldx, worldy)

  def check_tile(self, worldx:float, worldy:float) -> bool:
    return self._texture_layer_maps[self.editing_layer].check_tile(worldx, worldy)

  def update_tile_texture(self, worldx:float, worldy:float, bitmask:int, variant:int) -> Any:
    return self._texture_layer_maps[self.editing_layer].update_tile_texture(worldx, worldy, bitmask, variant)

  def get_map(self, query:pygame.Rect) -> list[point2d, pygame.Surface]:
    textures = []
    for layer in self._texture_layers:
      textures.extend(self._texture_layer_maps[layer].get_terrain(query))

    return textures