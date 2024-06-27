import pygame

try:
  from .elems import Singleton
except:
  from elems  import Singleton

DEFAULT : str = 'def'
GLOW_Z : int = 63

class Render(Singleton):
  'render singleton that is orders rendering'

  def __init__(self, groups:list=None):
    super().__init__()

    self.groups : list = groups if groups != None else [DEFAULT]
    self.render_groups : dict = {}
    for group in self.groups:
      self.render_groups[group] = []

  # flushes out everything in the render pipe
  def flush(self) -> None:
    'flushes all render calls out of the render queue'
    for group in self.groups:
      self.render_groups[group] = []

  # takes a surface and adds it to the rendering queue
  def draw(self, surf:pygame.Surface, pos:tuple, z:int=0, group:str=DEFAULT) -> None:
    'queues a simple blit call for surface rendering'
    self.render_groups[group].append((z, surf, pos))

  # takes a render func with its args and kwargs and adds it to the rendering queue
  def drawf(self, func:callable, *args, **kwargs) -> None:
    'queues a function reference draw'
    z = kwargs['z'] if 'z' in kwargs else 0
    group = kwargs['group'] if 'group' in kwargs else DEFAULT
    if 'z' in kwargs: del kwargs['z']
    if 'group' in kwargs: del kwargs['group']

    self.render_groups[group].append((z, func, args, kwargs))

  # renders to the destination surfaces, does it in place
  def render(self, dests:dict) -> None:
    'performs all queued render calls and flushes the render queue'
    for group in dests:
      if group not in self.render_groups:
        continue

      self.render_groups[group].sort(key=lambda data : data[0])

      for data in self.render_groups[group]:
        if len(data) > 3:
          _, func, args, kwargs = data
          func(dests[group], *args, **kwargs)
        else:
          if data[0] != GLOW_Z:
            dests[group].blit(data[1], data[2])
          else:
            dests[group].blit(data[1], data[2], special_flags=pygame.BLEND_RGBA_ADD)

    self.flush()