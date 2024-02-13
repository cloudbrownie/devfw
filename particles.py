import pygame
import time

from typing import Generator

try:
  from .elems import Element
except:
  from elems  import Element

class Particle(Element):
  def __init__(self, pos:pygame.Vector2=pygame.Vector2(),
               vel:pygame.Vector2=pygame.Vector2(), life_time:float=0):
    super().__init__()
    self.life_time : float          = life_time
    self.pos       : pygame.Vector2 = pos
    self.vel       : pygame.Vector2 = vel

  @property
  def is_dead(self) -> bool:
    return self.life_time == 0

  def move(self) -> None:
    self.pos += self.vel * self.elements['Window'].dt

  def update(self) -> None:
    ...

class Emitter(Element):
  def __init__(self, p_type:object, pool_size:int=0,
               source:pygame.Vector2=pygame.Vector2(), vel_range:tuple=(0,0),
               ang_range:tuple=(0,0), emit_delay:float=999999999):
    super().__init__()
    self.pool           : list   = []
    self.particle_index : int    = 0
    self.particle_type  : object = p_type
    for _ in range(pool_size):
      self.pool.append(p_type())

    self.emitting   : bool = False
    self.emit_delay : float = emit_delay
    self.last_emit  : float = 0
    self.source     : pygame.Vector2 = source
    self.vel_range  : tuple = vel_range
    self.ang_range  : tuple = ang_range

  def modify_size(self, new_size:int) -> None:
    if new_size > len(self.pool):
      for _ in range(new_size - len(self.pool)):
        self.pool.append(Particle)

    elif new_size < len(self.pool):
      for _ in range(len(self.pool) - new_size):
        self.pool.pop(-1)

      self.particle_index = min(self.particle_index, new_size - 1)

  def update(self) -> None:
    # emit particles if toggled, pool still has room, and delay has passed
    if self.emitting and self.particle_index < len(self.pool) and \
        time.time() - self.last_emit >= self.emit_delay:
      self.last_emit = time.time()
      self.pool[self.particle_index].life_time = 10
      self.pool[self.particle_index].pos
      self.pool[self.particle_index].vel

    for i in range(self.particle_index):
      # if particle is dead, swap to back
      if self.pool[i].is_dead:
        p = self.pool[self.particle_index]
        self.pool[self.particle_index] = self.pool[i]
        self.pool[i] = p
        self.particle_index -= 1
        continue

      # otherwise, update particle
      self.pool[i].update()

  def set_emit_source(self, x:int, y:int) -> None:
    self.source.update(x, y)

  def set_emit_params(self, vel_range:tuple, ang_range:tuple) -> None:
    self.vel_range = vel_range
    self.ang_range = ang_range

  def change_particle_type(self, p_type:object) -> None:
    self.particle_type = p_type
    for i in range(len(self.pool)):
      self.pool[i] = p_type()

  def emit_toggle(self, boolean:bool=None) -> None:
    if not boolean:
      self.emitting = not self.emitting
    else:
      self.emitting = boolean

  @property
  def alive_particles(self) -> Generator[Particle, None, None]:
    for i in range(self.particle_index):
      yield self.pool[i]
