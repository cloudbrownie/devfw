import pygame
import time

try:
  from .elems import Singleton
  from .mgl   import MGL, RenderObject
  from .utils import read_file
except:
  from elems  import Singleton
  from mgl    import MGL, RenderObject
  from utils  import read_file


class Window(Singleton):
  def __init__(self, width:int, height:int, caption:str='template', opengl=False, icon_path:str=None, vert_path:str=None, frag_path:str=None):
    super().__init__()
    pygame.init()
    pygame.display.set_caption(caption)
    self.caption : str = caption

    flags = pygame.OPENGL | pygame.DOUBLEBUF if opengl else 0

    self.window : pygame.Surface = pygame.display.set_mode((width, height), flags)

    if icon_path:
      pygame.display.set_icon(pygame.image.load(icon_path))

    self.clock : pygame.time.Clock = pygame.time.Clock()
    self.start_time : float = time.time()
    self.fps_limit : int = 144
    self.dt : float = 0
    self.rt : float = 0

    self.lowest : int = 60
    self.lowest_last_update : float = time.time()
    self.lowest_refresh_time : float = 1.5

    self.bg_color : tuple = 30, 35, 40

    self.render_obj : RenderObject = None
    if opengl:
      MGL()
      if vert_path == None and frag_path == None:
        self.render_obj = self.elements['MGL'].create_render_object_default()
      else:
        self.render_obj = self.elements['MGL'].create_render_object(frag_path=frag_path, vert_path=vert_path, default=True)

  def show_debug(self) -> None:
    t = time.time()
    fps = round(1 / self.dt)
    if fps < self.lowest or t - self.lowest_last_update >= self.lowest_refresh_time:
      self.lowest = fps
      self.lowest_last_update = t
    pygame.display.set_caption(f'{self.caption} | FPS: {fps}/{self.lowest}')

  def update(self, uniforms:dict=None) -> None:
    if uniforms == None:
      uniforms = {}

    if self.render_obj:
      if self.render_obj.default and ('surf' not in uniforms):
        uniforms['surf'] = self.window
      self.render_obj.render(uniforms=uniforms)
    pygame.display.flip()
    self.window.fill(self.bg_color)
    if self.render_obj:
      self.elements['MGL'].context.clear(*[self.bg_color[i] / 255 for i in range(3)], 1.0)
    self.dt = min(max(self.clock.tick(self.fps_limit) / 1000, 1 / self.fps_limit), 1)
    self.rt = time.time() - self.start_time
