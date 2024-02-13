# rewritten from
class Element:
  def __init__(self, unique_id:str='', singleton:bool=False, register:bool=False):
    self.elements : Glob = elements
    self._name : str = self.__class__.__name__ if unique_id == '' else unique_id
    self._singleton : bool = singleton
    if register:
      self.elements.register(self)

  def update(self) -> None:
    pass

  def delete(self) -> None:
    self.elements.delete(self)

class Singleton(Element):
  def __init__(self):
    super().__init__(singleton=True, register=True)

class Glob:
  def __init__(self):
    self.elements : dict = {'duplicates': {}, 'singletons': {}}

  def register(self, element:Element) -> None:
    if element._singleton:
      self.elements['singletons'][element._name] = element
    elif element._name not in self.elements['duplicates']:
      self.elements['duplicates'][element._name] = [element]
    else:
      self.elements['duplicates'][element._name].append(element)

  # deletes from duplicates, no ability to delete singletons
  def delete(self, element:Element) -> None:
    if not element._singleton and element._name in self.elements['duplicates']:
      self.elements['duplicates'][element._name].remove(element)

  # grabs singletons
  def __getitem__(self, name:str) -> Element:
    return self.elements['singletons'][name]

  def get_group(self, key:str) -> list[Element]: # type: ignore
    return self.elements['duplicates'].get(key, [])

elements = Glob()