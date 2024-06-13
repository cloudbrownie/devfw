from functools import partial
from typing import NamedTuple

def read_file(path:str) -> str:
  f = open(path, 'r')
  data = f.read()
  f.close()
  return data

def bind_func(func:callable, *args, **kwargs) -> callable:
  return partial(func, *args, **kwargs)

class size2d(NamedTuple):
  w: float
  h: float

class point2d(NamedTuple):
  x: float
  y: float