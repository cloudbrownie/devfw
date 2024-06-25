from functools import partial
from dataclasses import dataclass

def read_file(path:str) -> str:
  f = open(path, 'r')
  data = f.read()
  f.close()
  return data

def bind_func(func:callable, *args, **kwargs) -> callable:
  return partial(func, *args, **kwargs)

@dataclass
class size2d:
  w: float
  h: float

  def __str__(self) -> str:
    return f'({self.w}, {self.h})'
  
@dataclass
class point2d:
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

  print(a, b, c, d)