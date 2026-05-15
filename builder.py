from build123d import *
from build123d import scale as b123d_scale
import sys
import os

from .aml import AMLModel, FACE_NORMALS
from .logo import load_svg, extrude_svg, logo_part_isolated
from .exports import export_all
from .drawing import export_drawing
from .core import step as log_step


def _orient_to_face(part, face, x, y, z):
    norm = FACE_NORMALS.get(face, (0, 0, 1))
    loc  = Location((x, y, z))
    if norm == (0,  0,  1): return loc * part
    if norm == (0,  0, -1): return loc * (Rotation(180, 0, 0) * part)
    if norm == (0, -1,  0): return loc * (Rotation( 90, 0, 0) * part)
    if norm == (0,  1,  0): return loc * (Rotation(-90, 0, 0) * part)
    if norm == (-1, 0,  0): return loc * (Rotation(  0, 90, 0) * part)
    if norm == ( 1, 0,  0): return loc * (Rotation(  0,-90, 0) * part)
    return loc * part


def _build_primitive(p):
    t       = p['type']
    x, y, z = p['x'], p['y'], p['z']
    w, d, h  = p['w'], p['d'], p['h']
    r        = p['radius']
    depth    = p['depth']
    rx, ry, rz = p['rotate_x'], p['rotate_y'], p['rotate_z']
    face     = p['face']
    subtract = p['subtract']
    part     = None

    if t == 'box':
        with BuildPart() as bp:
            Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        part = bp.part

    elif t == 'cylinder':
        with BuildPart() as bp:
            Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        part = bp.part

    elif t == 'pipe':
        with BuildPart() as bp:
            Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
            Cylinder(max(r - depth, 0.5), h, mode=Mode.SUBTRACT,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
        part = bp.part

    elif t == 'sphere':
        with BuildPart() as bp:
            Sphere(r)
        part = bp.part

    elif t == 'panel':
        with BuildPart() as bp:
            Box(w, depth, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        part = bp.part

    elif t == 'roof':
        with BuildPart() as bp:
            Box(w, d, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
        part = bp.part

    elif t == 'arch':
        with BuildPart() as bp:
            outer_r = w / 2
            inner_r = max(outer_r - depth, 0.5)
            with BuildSketch() as sk:
                with BuildLine():
                    Line((-outer_r, 0), (-inner_r, 0))
                    RadiusArc((-inner_r, 0), (inner_r, 0), inner_r)
                    Line((inner_r, 0), (outer_r, 0))
                    RadiusArc((outer_r, 0), (-outer_r, 0), -outer_r)
                make_face()
            extrude(amount=d)
        part = bp.part

    elif t == 'grid':
        rows = max(int(p['rows']), 1)
        cols = max(int(p['cols']), 1)
        sp   = p['spacing']
        cell_w = (w - sp * (cols + 1)) / cols
        cell_h = (h - sp * (rows + 1)) / rows
        parts  = []
        for row in range(rows):
            for col in range(cols):
                cx = -w/2 + sp + cell_w/2 + col * (cell_w + sp)
                cz =        sp + cell_h/2 + row * (cell_h + sp)
                with BuildPart() as bp:
                    with Locations(Location((cx, 0, cz))):
                        Box(cell_w, depth, cell_h,
                            align=(Align.CENTER, Align.CENTER, Align.CENTER))
                parts.append(bp.part)
        if parts:
            part = parts[0]
            for pp in parts[1:]:
                part = part + pp

    elif t == 'logo':
        svg_path = p.get('svg', '')
        size     = max(w, h) if max(w, h) > 0 else 35
        # CRITICAL FIX: fresh isolated BuildPart on every call.
        # Sharing the same ShapeList across multiple extrude() calls
        # causes OCCT to hang indefinitely — learned from 4h of debugging.
        part = logo_part_isolated(svg_path, size, depth)

    elif t == 'text':
        with BuildPart() as bp:
            with BuildSketch() as sk:
                Text(p.get('text','?'), font_size=p.get('font_size', 8),
                     align=(Align.CENTER, Align.CENTER))
            extrude(amount=depth)
        part = bp.part

    if part is None:
        return None, subtract

    # apply explicit rotate_x/y/z FIRST, then face orientation
    if rx != 0 or ry != 0 or rz != 0:
        part = Rotation(rx, ry, rz) * part

    part = _orient_to_face(part, face, x, y, z)
    return part, subtract


def build_aml(model, output_dir='.', draw=True, exports=True):
    name  = model.name
    total = len(model.primitives)

    print(f'\nArchitect — building: {name}')
    print(model.summary())
    print()

    errs = model.validate()
    if errs:
        print('Validation warnings:')
        for e in errs:
            print(f'  ! {e}')
        print()

    adds, subs = [], []

    for i, p in enumerate(model.primitives):
        label = p.get('label') or p['type']
        log_step(i + 1, total, label)
        try:
            part, subtract = _build_primitive(p)
        except Exception as e:
            print(f'  ERROR building {label}: {e}')
            continue
        if part is None:
            print('  skipped')
            continue
        if subtract:
            subs.append(part)
        else:
            adds.append(part)

    if not adds:
        print('Nothing to build.')
        return None

    print('\nMerging...')
    result = adds[0]
    for pp in adds[1:]:
        result = result + pp
    for pp in subs:
        result = result - pp

    os.makedirs(output_dir, exist_ok=True)
    stem = os.path.join(output_dir, name)

    if exports:
        print('\nExporting STEP + STL...')
        export_all(result, stem)

    if draw:
        print('\nGenerating drawing...')
        export_drawing(
            result,
            out_path=stem + '_drawing.svg',
            title=model.drawing_title or name.upper(),
            subtitle=model.drawing_subtitle or '',
            number=model.drawing_number,
            model_h=model.height,
        )

    print(f'\nDone: {output_dir}/')
    return result
