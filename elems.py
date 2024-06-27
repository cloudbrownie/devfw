class Element:
  'base class for all objects in the project, gives access to global singletons'

  def __init__(self, unique_id:str='', singleton:bool=False, register:bool=False):
    self.elements : Glob = elements
    self._name : str = self.__class__.__name__ if unique_id == '' else unique_id
    self._singleton : bool = singleton
    if register:
      self.elements.register(self)

  def update(self) -> None:
    'base overload method'
    pass

  def delete(self) -> None:
    'removes element from global access'
    self.elements.delete(self)

class Singleton(Element):
  'base class for singleton objects with global access'

  def __init__(self):
    super().__init__(singleton=True, register=True)

class Glob:
  'global access point for all elements'

  def __init__(self):
    self.elements : dict = {'duplicates': {}, 'singletons': {}}

  def register(self, element:Element) -> None:
    'registers an element to the global access point'
    if element._singleton:
      self.elements['singletons'][element._name] = element
    elif element._name not in self.elements['duplicates']:
      self.elements['duplicates'][element._name] = [element]
    else:
      self.elements['duplicates'][element._name].append(element)

  # deletes from duplicates, no ability to delete singletons
  def delete(self, element:Element) -> None:
    'removes an element from global access'
    if not element._singleton and element._name in self.elements['duplicates']:
      self.elements['duplicates'][element._name].remove(element)

  # grabs singletons
  def __getitem__(self, name:str) -> Element:
    'returns singleton objects with the same class name'
    return self.elements['singletons'][name]

  def get_group(self, key:str) -> list[Element]:
    'returns simple elements objects'
    return self.elements['duplicates'].get(key, [])

elements = Glob()