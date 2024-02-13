import moderngl
import pygame

from array import array

from .glob import Element, Singleton
from .utils import read_file

def_vert_shader = '''
#version 330 core

in vec2 vert;
in vec2 texcoord;
out vec2 uv;

void main() {
  uv = texcoord;
  gl_Position = vec4(vert, 0.0, 1.0);
}
'''

def_frag_shader = '''
#version 330

uniform sampler2D surf;

in vec2 uv;
out vec4 f_color;

void main() {
  f_color = vec4(texture(surf, uv).rgb, 1.0);
}
'''

class RenderObject(Element):
  def __init__(self, frag_shader:str, vert_shader:str=def_vert_shader, default:bool=False, vao_args:list=['2f 2f', 'vert', 'texcoord'], buffer=None):
    super().__init__()
    self.default = default
    self.vert_shader : str = vert_shader
    self.frag_shader : str = frag_shader
    self.program : moderngl.Program = self.elements['MGL'].context.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
    if not buffer:
      buffer = self.elements['MGL'].quad_buffer
    self.vertex_array : moderngl.VertexArray = self.elements['MGL'].context.vertex_array(self.program, [(buffer, *vao_args)])
    self.buffer : list = []

  def update(self, uniforms:dict={}) -> None:
    texture_id = 0
    uniform_list = list(self.program)
    for uniform in uniforms:
      if uniform not in uniform_list:
        continue
      if type(uniforms[uniform]) == moderngl.Texture:
        uniforms[uniform].use(texture_id)
        self.program[uniform].value = texture_id
        texture_id += 1
      else:
        self.program[uniform].value = uniforms[uniform]

  def convert_surfaces(self, uniforms:dict={}) -> None:
    for uniform, value in uniforms.items():
      if type(value) == pygame.Surface:
        texture = self.elements['MGL'].surf_to_tex(value)
        uniforms[uniform] = texture
        self.buffer.append(texture)
    return uniforms

  def render(self, dest=None, uniforms:dict={}) -> None:
    dest = dest if dest else self.elements['MGL'].context.screen

    dest.use()
    uniforms = self.convert_surfaces(uniforms)
    self.update(uniforms)
    self.vertex_array.render(moderngl.TRIANGLE_STRIP)

    for texture in self.buffer:
      texture.release()
    self.buffer = []

class MGL(Singleton):
  def __init__(self):
    super().__init__()

    self.context : moderngl.Context = moderngl.create_context()
    self.quad_buffer : moderngl.Buffer = self.context.buffer(data=array('f', [
      -1.0, 1.0, 0.0, 0.0,  # topleft
      -1.0, -1.0, 0.0, 1.0, # topright
      1.0, 1.0, 1.0, 0.0,   # bottomleft
      1.0, -1.0, 1.0, 1.0   # bottomright
    ]))

    self.default_vert : str = def_vert_shader
    self.default_frag : str = def_frag_shader

  def create_render_object_default(self) -> RenderObject:
    return RenderObject(self.default_frag, default=True)

  def create_render_object(self, frag_path:str, vert_path:str=None, vao_args:list=['2f 2f', 'vert', 'texcoord'], buffer=None) -> RenderObject:
    frag_shader = read_file(frag_path)
    vert_shader = read_file(vert_path) if vert_path else self.default_vert
    return RenderObject(frag_shader, vert_shader=vert_shader, vao_args=vao_args, buffer=buffer)

  def surf_to_tex(self, surf:pygame.Surface) -> moderngl.Texture:
    texture = self.context.texture(surf.get_size(), 4)
    texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
    texture.swizzle = 'BGRA'
    texture.write(surf.get_view('1'))
    return texture