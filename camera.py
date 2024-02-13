import pygame

from .glob import Singleton

class Camera(Singleton):
  MIN_SIZE : tuple = 100, 100

  def __init__(self, width:int, height:int, sx:int=0, sy:int=0):
    super().__init__()
    self.width  : int = width
    self.height : int = height

    self.rect : pygame.Rect = pygame.Rect(0, 0, width, height)

    self.scroll_pos : pygame.Vector2 = pygame.Vector2(sx, sy)
    self.scroll_tgt : pygame.Vector2 = pygame.Vector2(sx, sy)

    self.rect.center = self.scroll_pos

    self.scroll_coeff   : float = 1
    self.scroll_minstep : float = 0.2
    self.scroll_thresh  : float = 0.25

    self.scroll_pause : bool = False

  def reset_scroll(self, x:int=0, y:int=0) -> None:
    self.scroll_pos.update(x=x, y=y)
    self.scroll_tgt.update(x=x, y=y)

  def move_scroll(self, x:int, y:int, immediate:bool=True) -> None:
    self.scroll_tgt.x -= x
    self.scroll_tgt.y -= y
    if immediate:
      self.scroll_pos.x -= x
      self.scroll_pos.y -= y

  def update_scroll(self, dt:float) -> None:
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
    self.scroll_pause = boolean

  def set_size_update(self, boolean:bool) -> None:
    self.dim_pause = boolean

  def update(self) -> None:
    if not self.scroll_pause and (self.scroll_pos != self.scroll_tgt):
      self.update_scroll(self.elements['Window'].dt)