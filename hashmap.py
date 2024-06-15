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


class Chunk:
  'used for storing data in chunks for spatial hash'
  def __init__(self, chunk_pos:point2d, chunk_width:int, tile_size:int):
    self.chunk_pos : point2d = chunk_pos
    self.chunk_width : int = chunk_width
    self.chunk_size : int = chunk_width * tile_size
    self.tile_size : int = tile_size
    self.grid : list[list[Any]] = [[None for _ in range(chunk_width)] for _ in range(chunk_width)]
    self.count : int = 0

  def add_item(self, row:int, col:int, data:Any) -> None:
    'add item to chunk at <row>, <col>'
    if self.grid[row][col] == None:
      self.count += 1
    self.grid[row][col] = data

  def del_item(self, row:int, col:int) -> Any:
    'returns item in chunk at <row>, <col> and deletes it'
    if self.grid[row][col] != None:
      self.count -= 1
    item = self.grid[row][col]
    self.grid[row][col] = None
    return item
  
  def get_item(self, row:int, col:int) -> Any:
    'returns item in chunk at <row>, <col>'
    return self.grid[row][col]

  def check_item(self, row:int, col:int) -> bool:
    'returns boolean of item status at <row>, <col>'
    return self.get_item(row, col) != None

  def swap_item(self, row:int, col:int, data:Any) -> Any:
    'returns item in chunk at <row>, <col> and replaces with new item'
    item = self.grid[row][col]
    self.grid[row][col] = data
    return item
  

class HashMap(Element):
  'generic spatial hash implementation'
  def __init__(self, chunk_width:int=16):
    super().__init__()

    self.chunks : dict[str, Chunk] = {}
    self.CHUNK_WIDTH : int = chunk_width