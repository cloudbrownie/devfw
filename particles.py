import pygame
import time
import random

from enum import IntEnum
from typing import Generator

try:
  from .elems import Element
except:
  from elems  import Element

# used in the emitter class
class PARAMETER_TYPES(IntEnum):
  PASS = 1
  RANDI = 2
  RANDF = 3

# base particle class, inherited by all other particles
class Particle(Element):
  'base particle template class'

  def __init__(self, pos:pygame.Vector2=None):
    super().__init__()
    self.dead : bool = False

    self.pos : pygame.Vector2 = pygame.Vector2() if not pos else pos

  # can overload this in inheritors
  def is_dead(self) -> bool:
    'returns if particle is dead'
    return self.dead

  # overload in inheritors
  def reset(self) -> None:
    'set particle to alive'
    self.dead = False

  def set_pos(self, x:float, y:float) -> None:
    'sets the position of the particle'
    self.pos.update(x, y)

  def set_kwargs(self) -> None:
    'base method for overload. sets keyword arguments for custom particles'
    return NotImplementedError

  def update(self) -> None:
    'base method for overload. called every frame to update particle logic'
    return NotImplementedError

# emits particles
class Emitter(Element):
  'emits particles from a particle pool at a certain location with loaded keyword arguments'

  def __init__(
      self,
      pool:'ParticlePool', # type: ignore
      source:pygame.Vector2=None,
      emit_delay:float=999999999,
      force:bool=False,
      params:dict=None,
      param_flags:dict=None
    ):

    super().__init__()
    self.pool        : ParticlePool   = pool
    self.force       : bool           = force
    self.emitting    : bool           = False
    self.emit_delay  : float          = emit_delay
    self.last_emit   : float          = 0
    self.source      : pygame.Vector2 = source if source else pygame.Vector2()
    self.params      : dict           = params if params else {}
    self.param_flags : dict           = param_flags if param_flags else {}

  def update(self) -> None:
    'called every frame and emits particles if possible'
    if self.emitting and time.time() - self.last_emit >= self.emit_delay:
      self.last_emit = time.time()

      parameters = {}
      for parameter in self.params:
        if self.param_flags[parameter] == PARAMETER_TYPES.PASS:
          parameters[parameter] = self.params[parameter]
        elif self.param_flags[parameter] == PARAMETER_TYPES.RANDI:
          parameters[parameter] = random.randint(*self.params[parameter])
        elif self.param_flags[parameter] == PARAMETER_TYPES.RANDF:
          parameters[parameter] = random.uniform(*self.params[parameter])

      self.pool.create_particle(self.source.xy, force=self.force, **parameters)

  def set_emit_source(self, x:int, y:int) -> None:
    'moves the emitter to emit from x, y'
    self.source.update(x, y)

  def set_emit_params(self, params:dict, flags:dict=None) -> None:
    'sets the parameters for emitting particles'
    self.params = params

    if flags == None:
      flags = {}
    for parameter in params:
      if parameter not in flags:
        flags[parameter] = PARAMETER_TYPES.PASS

    self.param_flags = flags

  def toggle_emit(self, boolean:bool=None) -> None:
    'toggles the emitter to emit particles'
    if not boolean:
      self.emitting = not self.emitting
    else:
      self.emitting = boolean

  def toggle_force_emit(self, boolean:bool=None) -> None:
    'toggles whether the emitter will forcefully request particles from the pool to emit'
    if not boolean:
      self.force = not self.force
    else:
      self.force = boolean

class ParticlePool(Element):
  'a particle pool to manage and limit the number of particles of a certain type'

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
    'generates all particles from the pool'
    for i in range(self.particle_index):
      yield self.pool[i]

  @property
  def available(self) -> int:
    'number of unused and available particles from the pool'
    return len(self.pool) - self.particle_index

  # only call when forcing particles to be available
  def get_next(self, force:bool=False) -> Particle:
    'returns the next available particle'
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
    'resizes the particle pool'
    if new_size > len(self.pool):
      for _ in range(new_size - len(self.pool)):
        self.pool.append(Particle)

    elif new_size < len(self.pool):
      for _ in range(len(self.pool) - new_size):
        self.pool.pop(-1)

      self.particle_index = min(self.particle_index, new_size - 1)

  # changes particle type of particle pool
  def change_particle_type(self, p_type:object) -> None:
    'changes the particle type held by the pool'
    self.particle_type = p_type
    for i in range(len(self.pool)):
      self.pool[i] = p_type()

  # swaps position of particles in array
  def _swap_particles(self, i:int, j:int) -> None:
    'private method for reordering particles during management'
    p = self.pool[i]
    self.pool[i] = self.pool[j]
    self.pool[j] = p

  # creates a particle emitter
  def create_emitter(self, emit_delay:float) -> Emitter:
    'creates an emitter attached to this pool'
    self.emitters.append(Emitter(self, emit_delay=emit_delay))
    return self.emitters[-1]

  def create_particle(self, src:tuple, force:bool=False, **kwargs) -> None:
    'creates a particle from the pool'
    p = self.get_next(force)
    if p == None:
      return

    p.reset()
    p.set_pos(src[0], src[1])
    p.set_kwargs(**kwargs)

  def update(self) -> None:
    'called every frame to update the particle pool and attached emitters'
    for emitter in self.emitters:
      emitter.update()

    i = 0
    while i < self.particle_index:
      # otherwise, update particle
      self.pool[i].update()

      if self.pool[i].is_dead():
        self.pool[i].dead = True

        self.particle_index -= 1
        self._swap_particles(i, self.particle_index)

      i += 1