from build123d import *
from build123d import scale as b123d_scale
import os
import sys
import time


def step(n, total, msg):
    print(f'[{n}/{total}] {msg}')
    sys.stdout.flush()


def pipe(x, y, radius, height):
    with BuildPart() as p:
        with Locations(Location((x, y, 0))):
            Cylinder(radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return p.part


def box_part(x, y, z, w, d, h):
    with BuildPart() as p:
        with Locations(Location((x, y, z))):
            Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return p.part


def cylinder_cut(part, x, y, z, radius, height):
    with BuildPart() as p:
        add(part)
        with Locations(Location((x, y, z))):
            Cylinder(radius, height, mode=Mode.SUBTRACT)
    return p.part


def merge(*parts):
    result = parts[0]
    for p in parts[1:]:
        result = result + p
    return result
