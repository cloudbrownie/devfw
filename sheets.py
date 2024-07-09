import pygame
import json
import pprint
import os
import random

try:
  from .elems import Singleton
  from .utils import size2d
except:
  from elems  import Singleton
  from utils  import size2d

MARKER  : tuple = 255,  41, 250, 255
CONE    : tuple =  10, 249, 249, 255

class Sheets(Singleton):
  def __init__(self):
    super().__init__()

    self.sheets : dict = {}
    self.configs : dict = {}
    self.sheet_map : list = []

  def load_sheet(self, path:str, cfg:bool=True) -> None:

    name = path.split('/')[-1].removesuffix('.png')

    raw_sheet = pygame.image.load(path)

    self.sheets[name] = {'surf':raw_sheet, 'dat':[]}
    self.sheet_map.append(name)

    for j in range(raw_sheet.get_height()):
      if raw_sheet.get_at((0, j)) == MARKER:
        row = []
        x = 0
        for i in range(x, raw_sheet.get_width()):
          if raw_sheet.get_at((i, j)) == CONE:
            w = i - (x + 1)

            h = 1
            for k in range(j + 1, raw_sheet.get_height()):
              if raw_sheet.get_at((i, k)) == CONE:
                h = (k - 1) - (j)
                break

            tex = pygame.Surface((w, h))
            tex.set_colorkey((0, 0, 0))
            tex.blit(raw_sheet, (0, 0), (x + 1, j + 1, w, h))

            row.append(tex)

            x = i

        self.sheets[name]['dat'].append(row)

    if cfg:
      cfg_path = path.replace('.png', '.json')
      cfg_data = {}

      if os.path.exists(cfg_path):

        with open(cfg_path, 'r') as f:
          cfg_data = json.load(f)

        self.configs[name] = cfg_data

      else:

        self.configs[name] = {
          'bits':4,
          'offsets':[],
          'weights':[]
        }

        for row in range(len(self.sheets[name]['dat'])):
          self.configs[name]['offsets'].append([])
          self.configs[name]['weights'].append([])
          for i in range(len(self.sheets[name]['dat'][row])):
            self.configs[name]['offsets'][row].append((0, 0))
            self.configs[name]['weights'][row].append(1)

  def load_sheets(self, path_data:list[tuple[str, bool]]) -> None:
    for path, cfg in path_data:
      self.load_sheet(path, cfg)

  def get_sheet_names(self) -> list:
    return self.sheet_map.copy()
  
  def get_sheet_data(self, sheet_id:int) -> dict:
    sheet_name = self.sheet_map[sheet_id]
    data = {
      'surfs':self.sheets[sheet_name]['dat'].copy(),
      'cnfg':self.configs.get(sheet_name, None)
    }

    return data

  def get_texture(self, sheet_id:int, row:int, col:int) -> pygame.Surface:
    sheet_name = self.sheet_map[sheet_id]
    sheet_data = self.sheets[sheet_name]

    return sheet_data['dat'][row][col]
  
  def get_texture_offsets(self, sheet_id:int, row:int, col:int) -> tuple[int, int]:
    sheet_name = self.sheet_map[sheet_id]
    sheet_cnfg = self.configs[sheet_name]

    return sheet_cnfg['offsets'][row][col]

  
  def get_texture_size(self, sheet_id:int, row:int, col:int) -> tuple:
    sheet_name = self.sheet_map[sheet_id]
    sheet_data = self.sheets[sheet_name]

    return sheet_data['dat'][row][col].get_size()
  
  def get_random_texture_type(self, sheet_id:int, row:int) -> int:
    sheet_name = self.sheet_map[sheet_id]
    sheet_data = self.sheets[sheet_name]

    variants = len(sheet_data['dat'][row])

    if variants == 1:
      return 0

    sheet_cnfg = self.configs[sheet_name]

    return random.choices(range(variants), weights=sheet_cnfg['weights'][row])[0]

  def get_bitmask_offsets(self, sheet_id) -> list[tuple[int, int]]:
    sheet_name = self.sheet_map[sheet_id]
    sheet_cnfg = self.configs[sheet_name]

    if sheet_cnfg['bits'] == 8:
      return [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
    return [(0, -1), (-1, 0), (1, 0), (0, 1)]
  
  def rectify_bitmask(self, sheet_id:int, bitmask:int) -> int:
    sheet_name = self.sheet_map[sheet_id]
    sheet_cnfg = self.configs[sheet_name]

    if bitmask > 15 and sheet_cnfg['bits'] == 4:
      return 15
    
    elif sheet_cnfg['bits'] == 8:
      ...

    return bitmask

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
      height += row_height + 1
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
        output.set_at((x, y + rects[j][i].h), CONE)
        x += 1

      y += row_heights[j] + 1

    pygame.image.save(output, name)

    if gen_config_template:
      config = {
        'bits':4,
        'offsets':[],
        'weights':[]
      }

      for row in range(len(rects)):
        config['offsets'].append([])
        config['weights'].append([])
        for i in range(len(rects[row])):
          config['offsets'][row].append((0, 0))
          config['weights'][row].append(1)

      json_name = name.removesuffix('.png')
      with open(f'{json_name}.json', 'w') as f:
        f.write(pprint.pformat(config, indent=2).replace("'", '"'))