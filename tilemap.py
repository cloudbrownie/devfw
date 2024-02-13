try:
  from .elems import Singleton
except:
  from elems  import Singleton

class Tilemap(Singleton):
  def __init__(self, chunk_size:int=16, tile_size:int=16):
    super().__init__()

    self.chunks : dict = {}
    self.CHUNK_SIZE : int = chunk_size
    self.TILE_SIZE : int = tile_size

  def get_chunk_pos(self, worldx:float, worldy:float) -> tuple:
    return int(worldx / (self.CHUNK_SIZE * self.TILE_SIZE)), int(worldy / (self.CHUNK_SIZE * self.TILE_SIZE))

  def get_chunk_tag(self, worldx:float, worldy:float) -> str:
    cx, cy = self.get_chunk_pos(worldx, worldy)
    return f'{cx},{cy}'

  def get_grid_pos(self, worldx:float, worldy:float) -> tuple:
    return int(worldx / self.TILE_SIZE), int(worldy / self.TILE_SIZE)

  def get_tile_pos(self, worldx:float, worldy:float) -> tuple:
    return int(worldx - worldx % self.TILE_SIZE), int(worldy - worldy % self.TILE_SIZE)

  def add_tile(self, worldx:float, worldy:float, layer:int) -> None:
    chunk_tag = self.get_chunk_tag(worldx, worldy)

    if chunk_tag not in self.chunks:
      self.chunks[chunk_tag] = {}


    pass

  def remove_tile(self) -> None:
    pass