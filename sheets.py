import pygame

from .glob import Singleton

MARKER : tuple = 255, 0, 170, 255

class Sheets(Singleton):
  def __init__(self):
    super().__init__()

    self.sheets : dict = {}
    self.config : dict = {}

  def load_sheet(self, path:str, cfg_path:str=None) -> None:

    name = path.split('/')[-1].removesuffix('.png')

    raw_sheet = pygame.image.load(path)

    self.sheets[name] = {'surf':raw_sheet, 'dat':{}}

    for j in range(raw_sheet.get_height()):
      if raw_sheet.get_at((0, j)) == MARKER:
        for i in range(raw_sheet.get_width()):
          pass

  def get_asset(self, asset_id:str) -> pygame.Surface:
    name, dat = asset_id.split(';')
    if name not in self.sheets or dat not in self.sheets[name]['dat']:
      return None

    return self.sheets[name]['dat'][dat]

  def get_config(self, asset_id:str) -> None:
    name, dat = asset_id.split(';')
    if name not in self.config or dat not in self.config[name][dat]:
      return None

    return self.config[name][dat]