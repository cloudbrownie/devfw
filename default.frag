#version 330

uniform sampler2D surf;

in vec2 uv;
out vec4 f_color;

void main() {
  f_color = vec4(texture(surf, uv).rgb, 1.0);
}