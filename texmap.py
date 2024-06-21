import pygame

from typing import Any

try:
  from .spatialhash import Chunk, SpatialHashMap
  from .utils   import point2d
except:
  from scripts.devfw.spatialhash import Chunk, SpatialHashMap
  from utils   import point2d

class TexChunk(Chunk):
  def __init__(self, chunk_pos:point2d, chunk_width:int, tile_size:int):
    super().__init__(None, chunk_pos=chunk_pos, chunk_width=chunk_width, tile_size=tile_size)
    self.textures : list = []

  def get_textures(self) -> list:
    'returns list of (point2d, (sheet id, texture row, texture col)) of entire chunk'

    if self.outdated:
      self.textures = []    
      for row in range(len(self.chunk_width)):
        for col in range(len(self.chunk_width)):
          self.textures.append((point2d(col * self.tile_size + self.chunk_pos.x * self.chunk_size, row * self.tile_size + self.chunk_pos.y * self.chunk_size), self.grid[row][col]))

    return self.textures    

class TexSHMap(SpatialHashMap):
  def __init__(self, chunk_width:int=16, tile_size:int=16):
    super().__init__(TexChunk, chunk_width=chunk_width, tile_size=tile_size)

  def add_tile(self, worldx:float, worldy:float, sheet_id:int, tex_row:int, tex_col:int, ) -> None:
    super().add_tile(worldx, worldy, (sheet_id, tex_row, tex_col))

  def get_terrain(self, query:pygame.Rect, pad:bool=True) -> list[Any]:
    'returns list of (point2d, (sheet id, texture row, texture col)) tuples for rendering'
    tags = self.get_chunks_in_rect(query, pad)

    textures = []
    for tag in tags:
      textures.extend(self.chunks[tag].get_textures())

    return textures