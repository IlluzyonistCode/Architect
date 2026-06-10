import os
from build123d import *
from build123d import scale as b123d_scale

def load_svg(path, size):
    if not os.path.exists(path):
        print(f'  [logo] SVG not found: {path}')

        return

    shapes = import_svg(path)

    verts = []

    for s in shapes:
        if hasattr(s, 'vertices'):
            for v in s.vertices():
                verts.append((v.X, v.Y))

    if not verts:
        print('  [logo] SVG has no vertices')

        return

    min_x = min(v[0] for v in verts)
    max_x = max(v[0] for v in verts)
    min_y = min(v[1] for v in verts)
    max_y = max(v[1] for v in verts)

    orig_w = max_x - min_x
    orig_h = max_y - min_y

    if orig_w <= 0 or orig_h <= 0:
        print('  [logo] SVG bounding box is zero')

        return

    factor = size / max(orig_w, orig_h)
    shapes = b123d_scale(shapes, factor)

    verts2 = []

    for s in shapes:
        if hasattr(s, 'vertices'):
            for v in s.vertices():
                verts2.append((v.X, v.Y))

    if not verts2:
        return

    cx = (min(v[0] for v in verts2) + max(v[0] for v in verts2)) / 2
    cy = (min(v[1] for v in verts2) + max(v[1] for v in verts2)) / 2

    offset = Location((-cx, -cy, 0))

    return ShapeList([offset * s for s in shapes])

def _build_logo_isolated(svg_path, size, depth):
    shapes = load_svg(svg_path, size)

    if shapes is None or len(shapes) == 0:
        return

    with BuildPart() as bp:
        with BuildSketch() as sk:
            for shape in shapes:
                add(shape)

        extrude(amount=depth)

    return bp.part

def logo_part_isolated(svg_path, size, depth):
    part = _build_logo_isolated(svg_path, size, depth)

    if part is None:
        with BuildPart() as bp:
            Box(size, size, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))

        return bp.part

    return part

def extrude_svg(shapes, depth):
    with BuildPart() as p:
        with BuildSketch() as sk:
            for shape in shapes:
                add(shape)

        extrude(amount=depth)

    return p.part

def logo_part(svg_path, size, depth, fallback=True):
    return logo_part_isolated(svg_path, size, depth)

def place_logo(base_part, logo_p, x, y, z, rotate_x=0, rotate_y=0, rotate_z=0):
    rotated = Rotation(rotate_x, rotate_y, rotate_z) * logo_p
    placed = Location((x, y, z)) * rotated
    
    return base_part + placed
