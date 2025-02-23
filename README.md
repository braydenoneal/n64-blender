# N64 Blender

Nintendo 64 based graphics in Blender.

Borrowed heavily from [Fast64](https://github.com/Fast-64/fast64).

Todo
====

- [x] uv shift
- [x] color overlay
- [x] solid color objects
- [x] figure out ambient light and directional light = [image x ambient + image x directional]
- [x] figure out directional light strength calculation (normals)
- [x] ensure that lighting is correct (rgb color accuracy and light strength stuff)
- [x] figure out why texture is unstable = [blend mode alpha blend makes it unstable]
- [x] ambient color
- [x] directional light
- [x] translucency
- [x] global variables
- [x] set defaults for globals
- [x] reset sidebar options to default when creating new material
- [x] global overrides
- [x] vertex alpha
- [x] texture scale
- [ ] multiple textures (vertex alpha and separate uv maps too)
- [ ] convert panel classes to layout.panel
- [ ] split up functions, classes, and files (sub property groups, sub panels, etc.)
- [ ] world space light direction toggle
- [ ] post-processing: horizontal blur and large antialiasing
- [ ] skybox
- [ ] clean up nodes and ui (maybe convert back to curved routes)
- [ ] texture scroll
- [ ] texture animation
- [ ] color masked textures? (think colored bundles)
- [ ] global toggles (disable fog, etc. globally)
- [ ] geometry that always faces the camera
- [ ] create color attribute when a 4b material is selected, not just created
- [ ] Gouraud shading (see Documents/Blender/4b_specular_highlights_example.blend)
- [ ] fix texture clamp (it should be in all directions)

Later
-----

- particles
- collision
- object placement
- fix fog edge artifacts
- object pointers for shader data? (directional light object, ambient light object, fog object, etc.)
- smooth shading toggle?
- consider the fact that most color features can not make the original brighter
- consider the fact that black base color values are unaffected by most shading
- automatic vertex color tool based on configuration (ambient occlusion, light source, shadows)
- https://blender.stackexchange.com/questions/91204/how-to-bake-ambient-occlusion-into-vertex-colors (cycles on cuda)
