from functools import partial

def read_file(path:str) -> str:
  f = open(path, 'r')
  data = f.read()
  f.close()
  return data

def bind_func(func:callable, *args, **kwargs) -> callable:
  return partial(func, *args, **kwargs)
