from functools import partial
from dataclasses import dataclass

_base64chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

def read_file(path:str) -> str:
  f = open(path, 'r')
  data = f.read()
  f.close()
  return data

def bind_func(func:callable, *args, **kwargs) -> callable:
  return partial(func, *args, **kwargs)

def contains(x:float, y:float, w:float, h:float, pos:'point2d') -> bool:
  return x <= pos.x <= x + w and y <= pos.y <= y + h

def flatten(row:int, col:int, row_size:int) -> int:
  return row * row_size + col

def reshape(value:int, row_size:int) -> int:
  return value // row_size, value % row_size

@dataclass
class size2d:
  'simple size dataclass'
  w: float
  h: float

  def __str__(self) -> str:
    return f'({self.w}, {self.h})'
  
@dataclass
class point2d:
  'simple point dataclass'
  x: float
  y: float

  def copy(self) -> 'point2d':
    return point2d(self.x, self.y)

  def __add__(self, o) -> 'point2d':
    return point2d(self.x + o.x, self.y + o.y)
    
  def __sub__(self, o) -> 'point2d':
    return point2d(self.x - o.x , self.y - o.y)

  def __str__(self) -> str:
    return f'({self.x}, {self.y})'
  
if __name__ == '__main__':
  a = point2d(3, 4)
  b = point2d(1, 1)
  c = a + b
  d = a - b

  e = point2d(1, 1)

  print(a, b, c, d, b == e)