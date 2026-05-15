from build123d import *
from build123d import scale as b123d_scale
import os


def load_svg(path, size):
    if not os.path.exists(path):
        print(f'  [logo] SVG not found: {path}')
        return None

    shapes = import_svg(path)

    verts = []
    for s in shapes:
        if hasattr(s, 'vertices'):
            for v in s.vertices():
                verts.append((v.X, v.Y))

    if not verts:
        print('  [logo] SVG has no vertices')
        return None

    min_x = min(v[0] for v in verts)
    max_x = max(v[0] for v in verts)
    min_y = min(v[1] for v in verts)
    max_y = max(v[1] for v in verts)

    orig_w = max_x - min_x
    orig_h = max_y - min_y

    if orig_w <= 0 or orig_h <= 0:
        print('  [logo] SVG bounding box is zero')
        return None

    factor = size / max(orig_w, orig_h)
    shapes = b123d_scale(shapes, factor)

    verts2 = []
    for s in shapes:
        if hasattr(s, 'vertices'):
            for v in s.vertices():
                verts2.append((v.X, v.Y))

    if not verts2:
        return None

    cx = (min(v[0] for v in verts2) + max(v[0] for v in verts2)) / 2
    cy = (min(v[1] for v in verts2) + max(v[1] for v in verts2)) / 2

    # CRITICAL: use Location multiplication, NOT translate()
    offset = Location((-cx, -cy, 0))
    return ShapeList([offset * s for s in shapes])


def _build_logo_isolated(svg_path, size, depth):
    """
    Each call does a fresh import_svg + fresh BuildPart.
    Reusing the same ShapeList across multiple extrude() calls
    causes OCCT to hang — this is the fix from 4h of debugging.
    """
    shapes = load_svg(svg_path, size)
    if shapes is None or len(shapes) == 0:
        return None

    with BuildPart() as bp:
        with BuildSketch() as sk:
            for shape in shapes:
                add(shape)
        extrude(amount=depth)
    return bp.part


def logo_part_isolated(svg_path, size, depth):
    """
    Safe logo builder. Returns a standalone Part (not a ShapeList).
    Call once per logo placement — never share the return value
    between multiple Location placements (clone via Location * part instead).
    """
    part = _build_logo_isolated(svg_path, size, depth)
    if part is None:
        # fallback: flat box placeholder
        with BuildPart() as bp:
            Box(size, size, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
        return bp.part
    return part


# kept for backward compat
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
    placed  = Location((x, y, z)) * rotated
    return base_part + placed
