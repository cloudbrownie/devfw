import pygame

from typing import Any

try:
  from .spatialhash import Chunk, SpatialHashMap
  from .utils       import point2d, reshape, _base64chars
except:
  from spatialhash  import Chunk, SpatialHashMap
  from utils        import point2d, reshape, _base64chars


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
        offx, offy = self.elements['Sheets'].get_texture_offsets(sheet_id, tex_row, tex_col)
        self.cached_surf.blit(texture, (pos.x + offx + self.surf_buffer, pos.y + offy + self.surf_buffer))

      self.outdated = False

    return self.cached_surf
  
  def update_tile_texture(self, row:int, col:int, new_bitmask:int=-1, new_variant:int=-1) -> Any:
    'updates the tile texture info at row, col'
    sheet_id, old_row, old_col = self.get_item(row, col)

    new_row = new_bitmask if new_bitmask != -1 else old_row
    new_col = new_variant if new_variant != -1 else old_col

    return self.swap_item(row, col, (sheet_id, new_row, new_col))
  
  def get_save_data(self) -> Any:
    id_str = ''

    tex_types = []
    for i in range(self.chunk_width ** 2):
      row, col = reshape(i, self.chunk_width)
      data = self.grid[row][col]

      if data == None:
        id_str += 'x'
        continue

      data_id = 0

      if data not in tex_types:
        data_id = len(tex_types)
        tex_types.append(data)
      else:
        data_id = tex_types.index(data)

      data_id = _base64chars[data_id]

      id_str += f'{data_id}'

    data_str = ''
    run = 0
    for i in range(len(id_str)):
      if id_str[i] == 'x':
        run += 1
      else:
        if run > 0:
          data_str += f'.{run}.'
        run = 0
        data_str += id_str[i]

    data_str = data_str.removesuffix('.')

    tex_str = ''
    for (sheet_id, tex_row, tex_col) in tex_types:
      tex_str += f'{_base64chars[sheet_id]}{_base64chars[tex_row]}{_base64chars[tex_col]}.'

    tex_str = tex_str.removesuffix('.')

    return data_str + '|' + tex_str
  
  def reconstruct(self, data:Any) -> None:
    super().reconstruct()
    data_str, tex_str = data.split('|')

    # reconstruct texture data
    tex_data_types = []
    tex_types = [tex_type for tex_type in tex_str.split('.') if tex_type != '']
    for compressed in tex_types:
      sheet_id = _base64chars.index(compressed[0])
      tex_row  = _base64chars.index(compressed[1])
      tex_col  = _base64chars.index(compressed[2])

      tex_data_types.append((sheet_id, tex_row, tex_col))

    # reconstruct grid
    runs = data_str.split('.')
    running = runs[0] == ''
    if running:
      runs.pop(0)
    i = 0
    for run in runs:
      if running:
        i += int(run)
      else:
        for j in range(len(run)):
          row, col = reshape(i, self.chunk_width)
          self.grid[row][col] = tex_data_types[_base64chars.index(run[j])]
          i += 1

      running = not running

class TexSHMap(SpatialHashMap):
  'spatial hash structure for storing texture chunks'

  def __init__(self, chunk_width:int=16, tile_size:int=16):
    super().__init__(TexChunk, chunk_width=chunk_width, tile_size=tile_size)

  def add_tile(self, worldx:float, worldy:float, sheet_id:int, tex_row:int, tex_col:int) -> None:
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
  