import pygame
import sys
import functools
import time

try:
  from .elems import Singleton
  from .utils import bind_func
except: 
  from elems  import Singleton
  from utils  import bind_func

def _verify_key_modifiers(mods:int) -> bool:
    'determines if the pressed modifiers match the query'
    return pygame.key.get_mods() == mods or mods == KeyListener.IGNORE_MODS

class KeyListener:
  'used the input singleton to listen to keys and trigger functions'
  ONPRESS = 1
  CONTINUOUS = 2
  ONRELEASE = 3

  IGNORE_MODS = -1

  def __init__(self):
    self.pressed : bool = False
    self.keydown : bool = False
    self.keyup   : bool = False

    self.funcs : dict = {
      KeyListener.ONPRESS    : [],
      KeyListener.CONTINUOUS : [],
      KeyListener.ONRELEASE  : []
    }

  def update(self) -> None:
    'called every frame'
    self.keydown = False
    self.keyup   = False
    if self.pressed:
      # activate all functions bound to continuous mode
      for i, (func, _, (delay, last_update, mods)) in enumerate(self.funcs[KeyListener.CONTINUOUS]):

        if not _verify_key_modifiers(mods):
          continue

        if time.time() - last_update >= delay:
          self.funcs[KeyListener.CONTINUOUS][i][2][1] = time.time()
          func()

  def trigger(self) -> None:
    'calls the functions bound to onpress'
    self.pressed = True
    self.keydown = True
    self.keyup   = False
    for func, _, mods in self.funcs[KeyListener.ONPRESS]:
      if not _verify_key_modifiers(mods):
        continue
      func()

  def untrigger(self) -> None:
    'calls the functions bound to unpress'
    self.pressed = False
    self.keydown = False
    self.keyup   = True
    for func, _, mods in self.funcs[KeyListener.ONRELEASE]:
      if not _verify_key_modifiers(mods):
        continue
      func()

  def bind(self, func:callable, when:int, tag:str=None, delay:float=0.0, mods:int=0) -> None:
    'binds a function to this listener and sets conditions for calling them'
    if not tag:
      # if no custom tag, make function tag the function's name
      if type(func) == functools.partial:
        tag = func.func.__name__
      else:
        tag = func.__name__

    if when == KeyListener.CONTINUOUS:
      data = [delay, 0, mods]
    else:
      data = mods
    self.funcs[when].append((func, tag, data))

  def unbind(self, tag:str) -> None:
    'unbinds a function from this listener'
    for timing in self.funcs:
      for i, (_, func_tag, _) in enumerate(self.funcs[timing]):
        if func_tag == tag:
          self.funcs.pop(i)

  def reset(self) -> None:
    'clears all bound functions from this listener'
    for timing in self.funcs:
      self.funcs[timing].clear()

  def __str__(self) -> str:
    return f'Bool: {self.pressed} | Just Pressed: {self.keydown} | Just Released: {self.keyup}'

class MouseListener:
  'representation of the mouse for listening to mouse inputs'

  def __init__(self):
    self.pos : pygame.Vector2 = pygame.Vector2(0, 0)
    self.vel : pygame.Vector2 = pygame.Vector2(0, 0)

    self.m1 : KeyListener = KeyListener()
    self.m2 : KeyListener = KeyListener()
    self.m3 : KeyListener = KeyListener()

    self.wheel : pygame.Vector2 = pygame.Vector2(0, 0)
    self.wheel_func : callable = None

  @property
  def xy(self) -> tuple:
    'x, y position of the mouse'
    return self.pos.xy

  def click(self, button:int) -> None:
    'called to trigger the appropriate mouse button'
    match (button):
      case 1: # left click
        self.m1.trigger()
      case 3: # right click
        self.m2.trigger()
      case 2: # wheel click
        self.m3.trigger()

  def unclick(self, button:int) -> None:
    'called to untrigger the appropriate mouse button'
    match (button):
      case 1: # left click
        self.m1.untrigger()
      case 3: # right click
        self.m2.untrigger()
      case 2: # wheel click
        self.m3.untrigger()

  def update(self) -> None:
    'called every frame '
    if self.wheel_func and self.wheel != pygame.Vector2():
      self.wheel_func(*self.wheel.xy)

    self.wheel.update(0, 0)
    mx, my = pygame.mouse.get_pos()
    self.vel.x = mx - self.pos.x
    self.vel.y = my - self.pos.y

    self.pos.x = mx
    self.pos.y = my

    self.m1.update()
    self.m2.update()
    self.m3.update()

  def bind_wheel(self, func:callable) -> None:
    'binds a function to the mouse wheel'
    self.wheel_func = func

  def __str__(self) -> str:
    return f'Left Click:   {str(self.m1)}\nRight Click:  {str(self.m2)}\nMiddle Click: {str(self.m3)}'

class Input(Singleton):
  'singleton that controls all of the input handling for any game project'

  def __init__(self, app_name:str, custom_cursor:callable=None):
    super().__init__()

    self.app_name : str = app_name

    self.mouse : MouseListener = MouseListener()
    self.custom_cursor : bool = False
    self.custom_cursor_func : callable = None
    if custom_cursor:
      self.custom_cursor = True
      self.custom_cursor_func = bind_func(custom_cursor, position=self.mouse.pos)
      pygame.mouse.set_visible(False)

    self.keyboard_listeners : dict = {}

  @property
  def mouse_pos(self) -> pygame.Vector2:
    'returns the mouse position as a vector2d'
    return self.mouse.pos.copy()

  def bind_key(self, key:int, func:callable, when:int=KeyListener.ONPRESS, mods:int=0, delay:float=0.0) -> None:
    'binds a function to a specific key to be triggered based on \'when\' and given modifiers \'mods\''
    listener = self.keyboard_listeners.get(key, KeyListener())
    listener.bind(func, when, delay=delay, mods=mods)
    self.keyboard_listeners[key] = listener

  def update(self) -> None:
    'must be called every frame. clears pygame input buffer and triggers keybinds accordingly'

    if self.custom_cursor:
      self.elements['Render'].drawf(self.custom_cursor_func, z=1)

    self.mouse.update()

    # iterate over event buffer to obtain input events, may change later for event buffer stuff
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        self.elements[self.app_name].running = False

      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          self.elements[self.app_name].running = False

        if event.key in self.keyboard_listeners:
          self.keyboard_listeners[event.key].trigger()

      elif event.type == pygame.KEYUP:

        if event.key in self.keyboard_listeners:
          self.keyboard_listeners[event.key].untrigger()

      elif event.type == pygame.MOUSEBUTTONDOWN:
        self.mouse.click(event.button)

      elif event.type == pygame.MOUSEBUTTONUP:
        self.mouse.unclick(event.button)

      elif event.type == pygame.MOUSEWHEEL:
        self.mouse.wheel.update(event.x, event.y)

    for key in self.keyboard_listeners:
      self.keyboard_listeners[key].update()