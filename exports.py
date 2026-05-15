from build123d import *


def to_step(part, path):
    export_step(part, path)
    print(f'  STEP: {path}')


def to_stl(part, path, tolerance=0.5):
    export_stl(part, path, tolerance=tolerance)
    print(f'  STL:  {path}')


def export_all(part, stem):
    to_step(part, stem + '.step')
    to_stl(part, stem + '.stl')
