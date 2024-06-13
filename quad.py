
class QuadNode:
  def __init__(self, tree_ptr:'QuadTree'):
    self.tree : 'QuadTree' = tree_ptr
    self.ne : QuadNode = None
    self.nw : QuadNode = None
    self.se : QuadNode = None
    self.sw : QuadNode = None
    self.data : list = []

  def insert(self):
    ...

class QuadTree:
  def __init__(self, side_limit:int=16):
    self.root : QuadNode = None
    self.side_limit : int = side_limit

  def insert(self):
    ...

  def remove(self):
    ...

  def get(self):
    ...