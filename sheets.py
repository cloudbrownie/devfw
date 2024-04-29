import pygame
import json

try:
  from .elems import Singleton
except:
  from elems  import Singleton

MARKER  : tuple = 255,  41, 250, 255
CONE    : tuple =  10, 249, 249, 255

class Sheets(Singleton):
  def __init__(self):
    super().__init__()

    self.sheets : dict = {}
    self.config : dict = {}
    self.sheet_map : list = []

  def load_sheet(self, path:str, cfg:bool=False) -> None:

    name = path.split('/')[-1].removesuffix('.png')

    raw_sheet = pygame.image.load(path)

    self.sheets[name] = {'surf':raw_sheet, 'dat':[]}
    self.sheet_map.append(name)

    for j in range(raw_sheet.get_height()):
      if raw_sheet.get_at((0, j)) == MARKER:
        row = []
        x = 0
        for i in range(raw_sheet.get_width()):
          if raw_sheet.get_at((i, j)) == CONE:
            w = (i - 1) - (x + 1)

            h = 1
            for k in range(raw_sheet.get_height()):
              if raw_sheet.get_at((i, k)) == CONE:
                h = (k - 1) - (j + 1)

            tex = pygame.Surface((w, h))
            tex.blit(raw_sheet, (0, 0), (x + 1, j + 1, w, h))

            row.append(tex)

            x = i - 1

        self.sheets[name]['dat'].append(row)

    if cfg:
      cfg_path = path.replace('.png', '.json')
      cfg_data = {}
      with open(cfg_path, 'r') as f:
        cfg_data = json.load(f)

      self.config[name] = cfg_data

  def load_sheets(self, path_data:list[tuple[str, bool]]) -> None:
    for path, cfg in path_data:
      self.load_sheet(path, cfg)


  def get_tile_texture(self, tex:int, bitmask:int, variant:int) -> pygame.Surface:
    sheet_name = self.sheet_map[tex]
    sheet_data = self.sheets[sheet_name]

    # must pull from larger bitmask config
    if len(sheet_data['dat']) > 16:
      if tex in self.config and bitmask in self.config[tex]['map']:
        mapped = self.config[tex]['map']

        if variant > len(sheet_data[tex]['dat'][mapped]):
          return None

        return sheet_data[tex]['dat'][mapped][variant]

    # otherwise fine, 4 bit representation is direct index
    return sheet_data[tex]['dat'][bitmask][variant]

  def get_texture(self, tex:int, row:int, col:int) -> pygame.Surface:
    sheet_name = self.sheet_map[tex]
    sheet_data = self.sheets[sheet_name]

    return sheet_data[tex]['dat'][row][col]

  def get_tile_config(self, tex:int, bitmask:int, variant:int) -> pygame.Surface:
    sheet_name = self.sheet_map[tex]
    config_data = self.config[sheet_name]

    return config_data[tex]['offset'][bitmask][variant]

  def save_sheet(self, name:str, sheet:pygame.Surface, rects:list, gen_config_template:bool=False) -> None:

    # compute final size of sheet
    width = 0
    row_heights = []
    height = len(rects) + 1
    for row in rects:
      row_width = len(row) + 1
      row_height = 0
      for rect in row:
        row_width += rect.w
        row_height = max(row_height, rect.h)

      width = max(width, row_width)
      height += row_height
      row_heights.append(row_height)

    # make single surface
    output = pygame.Surface((width, height))

    y = 0
    for j in range(len(rects)):
      output.set_at((0, y), MARKER)
      x = 1
      y += 1
      for i in range(len(rects[j])):
        output.blit(sheet, (x, y), rects[j][i])
        x += rects[j][i].w
        output.set_at((x, y - 1), CONE)
        output.set_at((x, y + rect.h), CONE)
        x += 1

      y += row_heights[j]

    pygame.image.save(output, name)
