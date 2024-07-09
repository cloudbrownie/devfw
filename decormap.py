import pygame

from typing import Any

try:
  from .spatialhash import Chunk, SpatialHashMap
  from .utils       import point2d, contains, _base64chars
except:
  from spatialhash  import Chunk, SpatialHashMap
  from utils        import point2d, contains, _base64chars

class DecorChunk(Chunk):
  def __init__(self, chunk_pos:point2d, chunk_width:int, tile_size:int):
    super().__init__(None, chunk_pos=chunk_pos, chunk_width=chunk_width, tile_size=tile_size)
    self.textures     : list            = []
    self.cached_surf  : pygame.Surface  = None
    self.surf_buffer  : int             = 2

  def get_textures(self) -> list:
    'returns list of (point2d, (sheet id, texture row, texture col)) of entire chunk'
    return self.textures
  
  def add_decor(self, worldx:float, worldy:float, sheet_id:int, tex_row:int, tex_col:int) -> None:
    position = point2d(worldx, worldy)
    self.textures.append((position, (sheet_id, tex_row, tex_col)))
    self.count += 1
    self.outdated = True

  def del_decor(self, worldx:float, worldy:float) -> Any:
    world_pos = point2d(worldx, worldy)
    for i, (pos, (sheet_id, tex_row, tex_col)) in enumerate(self.textures):
      w, h = self.elements['Sheets'].get_texture_size(sheet_id, tex_row, tex_col)
      if contains(pos.x, pos.y, w, h, world_pos):
        self.textures.pop(i)
        self.count -= 1
        self.outdated = True
        return pos, sheet_id, tex_row, tex_col
    return None, None

  def get_chunk_texture(self) -> pygame.Surface:
    if self.outdated:
      self.cached_surf = pygame.Surface((self.chunk_size + self.surf_buffer, self.chunk_size + self.surf_buffer))
      self.cached_surf.set_colorkey((0, 0, 0))

      for (pos, (sheet_id, tex_row, tex_col)) in self.textures:
        texture = self.elements['Sheets'].get_texture(sheet_id, tex_row, tex_col)
        self.cached_surf.blit(texture, (pos.x - self.chunk_pos.x * self.chunk_size + self.surf_buffer, pos.y - self.chunk_pos.y * self.chunk_size + self.surf_buffer))

      self.outdated = False

    return self.cached_surf
  
  def get_save_data(self) -> Any:

    data_str = ''
    tex_types = []
    for (pos, data) in self.textures:
      data_id = 0
      if data not in tex_types:
        data_id = len(tex_types)
        tex_types.append(data)
      else:
        data_id = tex_types.index(data)

      data_id = _base64chars[data_id]

      data_str += f'{pos.x},{pos.y},{data_id}:'

    data_str = data_str.removesuffix(':')

    tex_str = ''
    for (sheet_id, tex_row, tex_col) in tex_types:
      tex_str += f'{_base64chars[sheet_id]}{_base64chars[tex_row]}{_base64chars[tex_col]}.'

    tex_str = tex_str.removesuffix('.')

    return data_str + '|' + tex_str
  
  def reconstruct(self, data:Any) -> None:
    super().reconstruct()
    self.textures = []
    data_str, tex_str = data.split('|')

    # reconstruct texture data
    tex_data_types = []
    tex_types = [tex_type for tex_type in tex_str.split('.') if tex_type != '']
    for compressed in tex_types:
      sheet_id = _base64chars.index(compressed[0])
      tex_row  = _base64chars.index(compressed[1])
      tex_col  = _base64chars.index(compressed[2])

      tex_data_types.append((sheet_id, tex_row, tex_col))

    # reconstruct textures
    textures = data_str.split(':')
    for texture in textures:
      x, y, compressed_tex = texture.split(',')

      pos = point2d(float(x), float(y))
      tex_data = tex_data_types[_base64chars.index(compressed_tex)]

      self.textures.append((pos, tex_data))


class DecorSHMap(SpatialHashMap):
  def __init__(self, chunk_width:int=16, tile_size:int=16):
    super().__init__(DecorChunk, chunk_width=chunk_width, tile_size=tile_size)

  def add_tile(self, worldx:float, worldy:float, sheet_id:int, tex_row:int, tex_col:int) -> None:
    w, h = self.elements['Sheets'].get_texture_size(sheet_id, tex_row, tex_col)

    for chunk_tag in self.get_chunks_in_rect(pygame.Rect(worldx, worldy, w, h), pad=False, include_empty=True):

      chunkx, chunky = self._unformat_chunk_tag(chunk_tag)

      if chunk_tag not in self.chunks:
        self.chunks[chunk_tag] = self.chunk_type(
          point2d(chunkx, chunky),
          self.CHUNK_WIDTH,
          self.TILE_SIZE
        )

      self.chunks[chunk_tag].add_decor(worldx, worldy, sheet_id, tex_row, tex_col)

  def del_tile(self, worldx:float, worldy:float, del_empty:bool=True) -> Any:
    chunkx, chunky = self.get_chunk_pos(worldx, worldy)
    chunk_tag = self._format_chunk_tag(chunkx, chunky)

    if chunk_tag not in self.chunks:
      return None
    
    pos, *data = self.chunks[chunk_tag].del_decor(worldx, worldy)
    if pos == None:
      return None

    if del_empty and self.chunks[chunk_tag].count == 0:
      del self.chunks[chunk_tag]

    # using found decor size, search in possible chunks for leftovers
    w, h = self.elements['Sheets'].get_texture_size(*data)
    for chunk_tag in self.get_chunks_in_rect(pygame.Rect(pos.x, pos.y, w, h)):
      
      if chunk_tag not in self.chunks:
        continue

      self.chunks[chunk_tag].del_decor(worldx, worldy)
      if self.chunks[chunk_tag].count == 0:
        del self.chunks[chunk_tag]

    return data

  def get_terrain(self, query:pygame.Rect, pad:bool=True) -> list[Any]:
    tags = self.get_chunks_in_rect(query, pad)
    
    textures = []
    for tag in tags:
      chunk_pos = self.chunks[tag].chunk_pos.copy()
      chunk_pos.x *= self.CHUNK_SIZE
      chunk_pos.y *= self.CHUNK_SIZE
      textures.append((chunk_pos, self.chunks[tag].get_chunk_texture()))

    return textures
  