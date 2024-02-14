import pygame
import time
import random
import math

from typing import Generator

try:
  from .elems import Element
except:
  from elems  import Element

# base particle class, inherited by all other particles
class Particle(Element):
  def __init__(self, pos:pygame.Vector2=None,
               vel:pygame.Vector2=None, life_time:float=0):
    super().__init__()
    self.life_time : float = life_time
    self.dead : bool = False

    self.pos : pygame.Vector2 = pygame.Vector2() if not pos else pos
    self.vel : pygame.Vector2 = pygame.Vector2() if not vel else vel

  # can overload this in inheritors
  def is_dead(self) -> bool:
    return self.dead

  def move(self) -> None:
    self.pos += self.vel * self.elements['Window'].dt

  def update(self) -> None:
    ...

# emits particles
class Emitter(Element):
  def __init__(
      self, 
      pool:'ParticlePool', # type: ignore
      source:pygame.Vector2=None, 
      vel_range:tuple=(0,0),
      ang_range:tuple=(0,0), 
      emit_delay:float=999999999,
      force:bool=False
    ):    

    super().__init__()
    self.pool       : ParticlePool   = pool
    self.force      : bool           = force
    self.emitting   : bool           = False
    self.emit_delay : float          = emit_delay
    self.last_emit  : float          = 0
    self.vel_range  : tuple          = vel_range
    self.ang_range  : tuple          = ang_range
    self.source     : pygame.Vector2 = source if source else pygame.Vector2()

  def update(self) -> None:
    if self.emitting and time.time() - self.last_emit >= self.emit_delay:
      self.last_emit = time.time()
      
      vel = random.uniform(self.vel_range[0], self.vel_range[1])
      ang = random.uniform(self.ang_range[0], self.ang_range[1])

      self.pool.create_particle(self.source.xy, vel, ang, self.force)

  def set_emit_source(self, x:int, y:int) -> None:
    self.source.update(x, y)

  def set_emit_params(self, vel_range:tuple, ang_range:tuple) -> None:
    self.vel_range = vel_range
    self.ang_range = ang_range

  def toggle_emit(self, boolean:bool=None) -> None:
    if not boolean:
      self.emitting = not self.emitting
    else:
      self.emitting = boolean

  def toggle_force_emit(self, boolean:bool=None) -> None:
    if not boolean:
      self.force = not self.force
    else:
      self.force = boolean

class ParticlePool(Element):
  def __init__(self, p_type:object, pool_size:int=0):
    super().__init__()
    self.pool           : list   = []
    self.particle_index : int    = 0 
    self.particle_type  : object = p_type
    for _ in range(pool_size):
      self.pool.append(p_type())

    self.emitters : list = []

  @property
  def alive_particles(self) -> Generator[Particle, None, None]:
    for i in range(self.particle_index):
      yield self.pool[i]

  @property
  def available(self) -> int:
    return len(self.pool) - self.particle_index
  
  # only call when forcing particles to be available
  def get_next(self, force:bool=False) -> Particle:
    # available
    if self.available > 0:
      p = self.pool[self.particle_index]
      self.particle_index += 1
      return p
  
    # none available but forcing one to be available
    elif self.available == 0 and force:
      sample_index = random.randint(0, len(self.pool) - 1)
      self._swap_particles(sample_index, len(self.pool) - 1)
      return self.pool[sample_index]

    return None
    
  def modify_size(self, new_size:int) -> None:
    if new_size > len(self.pool):
      for _ in range(new_size - len(self.pool)):
        self.pool.append(Particle)

    elif new_size < len(self.pool):
      for _ in range(len(self.pool) - new_size):
        self.pool.pop(-1)

      self.particle_index = min(self.particle_index, new_size - 1)

  # changes particle type of particle pool
  def change_particle_type(self, p_type:object) -> None:
    self.particle_type = p_type
    for i in range(len(self.pool)):
      self.pool[i] = p_type()

  # swaps position of particles in array
  def _swap_particles(self, i:int, j:int) -> None:
    p = self.pool[i]
    self.pool[i] = self.pool[j]
    self.pool[j] = p

  # creates a particle emitter
  def create_emitter(self, emit_delay:float) -> Emitter:
    self.emitters.append(Emitter(self, emit_delay=emit_delay))
    return self.emitters[-1]

  def create_particle(self, src:tuple, vel:float, ang:float, force:bool=False):
    p = self.get_next(force)
    if not p:
      return
    
    p.dead = False
    p.pos.update(src[0], src[1])
    p.vel.update(vel * math.cos(ang), vel * math.sin(ang))

  def burst(self, src:tuple, num:int, vel_range:tuple, ang_range:tuple, force:bool=False):
    for _ in range(num):
      vel = random.uniform(vel_range[0], vel_range[1])
      ang = random.uniform(ang_range[0], ang_range[1])
      self.create_particle(src, vel, ang, force)

  def update(self) -> None:
    for emitter in self.emitters:
      emitter.update()

    for i in range(self.particle_index):
      # otherwise, update particle
      self.pool[i].update()

      if self.pool[i].is_dead():
        self.pool[i].dead = True

        self._swap_particles(i, self.particle_index - 1)
        self.particle_index -= 1
