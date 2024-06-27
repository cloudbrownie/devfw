import pygame

try:
  from .elems import Element
except:
  from elems  import Element


class Camera(Element):
  'defines a 2d query area for rendering'
  MIN_SIZE : tuple = 100, 100

  def __init__(self, width:int, height:int, sx:int=None, sy:int=None, scoeff:float=1, sminstep:float=0.2, sthresh:float=0.25):
    super().__init__()
    self.width  : int = width
    self.height : int = height

    self.rect : pygame.Rect = pygame.Rect(0, 0, width, height)

    if sx == None and sy == None:
      sx = width / 2
      sy = height / 2

    self.scroll_pos : pygame.Vector2 = pygame.Vector2(sx, sy)
    self.scroll_tgt : pygame.Vector2 = pygame.Vector2(sx, sy)

    self.rect.center = self.scroll_pos

    # camera movement values
    self.scroll_coeff   : float = scoeff
    self.scroll_minstep : float = sminstep
    self.scroll_thresh  : float = sthresh

    # TODO: add dimension resizing values
    self.scroll_pause : bool = False

  def reset_scroll(self, x:int=0, y:int=0) -> None:
    'resets the camera\'s position to 0, 0'
    self.scroll_pos.update(x=x, y=y)
    self.scroll_tgt.update(x=x, y=y)

  def move_scroll(self, x:int, y:int, immediate:bool=True) -> None:
    'moves the camera\'s position by x, y'
    self.scroll_tgt.x += x
    self.scroll_tgt.y += y
    if immediate:
      self.scroll_pos.x += x
      self.scroll_pos.y += y
      self.rect.center = self.scroll_pos

  def update_scroll(self, dt:float) -> None:
    'called to interpolate camera position if current movement amount is not immediate'
    # compute amount to move and interpolate smoothly
    diff = self.scroll_tgt - self.scroll_pos
    if diff.magnitude() < self.scroll_thresh:
      self.scroll_pos.update(self.scroll_tgt)
      return

    step = diff * self.scroll_coeff * dt
    if step.magnitude() == 0:
      return

    if step.magnitude() < self.scroll_minstep:
      step.scale_to_length(self.scroll_minstep)

    self.scroll_pos += step
    self.rect.center = self.scroll_pos

  def set_scroll_update(self, boolean:bool) -> None:
    'set whether the camera\'s position is interpolating or not'
    self.scroll_pause = boolean

  def set_size_update(self, boolean:bool) -> None:
    'set whether the camera\'s size is interpolating or not '
    self.dim_pause = boolean

  def update(self) -> None:
    'called every frame for the camera move and resize properly'
    if not self.scroll_pause and (self.scroll_pos != self.scroll_tgt):
      self.update_scroll(self.elements['Window'].dt)