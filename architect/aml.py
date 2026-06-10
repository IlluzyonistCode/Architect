import json
import os
from dataclasses import dataclass, field, asdict

PRIMITIVE_TYPES = {
    'box', 'cylinder', 'pipe', 'sphere', 'cone', 'torus',
    'panel', 'roof', 'arch', 'prism', 'pyramid', 'wedge',
    'spring', 'thread', 'gear', 'slot', 'keyway',
    'grid', 'linear_array', 'polar_array',
    'logo', 'text',
    'mirror'
}

FACE_NORMALS = {
    'front': (0, -1, 0),
    'back': (0, 1, 0),
    'left': (-1, 0, 0),
    'right': ( 1, 0, 0),
    'top': (0, 0, 1),
    'bottom':(0, 0, -1)
}


@dataclass
class Primitive:
    type: str
    x: float = 0
    y: float = 0
    z: float = 0
    w: float = 10
    d: float = 10
    h: float = 10
    radius: float = 5
    depth: float = 2
    rotate_x: float = 0
    rotate_y: float = 0
    rotate_z: float = 0
    face: str = 'top'
    svg: str = ''
    text: str = ''
    font_size: float = 8
    rows: int = 3
    cols: int = 3
    spacing: float = 5
    subtract: bool = False
    label: str = ''
    radius2: float = 2
    turns: float = 5
    pitch: float = 3
    teeth: int = 12
    count: int = 3
    count_y: int = 1
    angle_total: float = 360
    dx: float = 20
    dy: float = 0
    dz: float = 0
    mirror_axis: str = 'x'
    targets: str = ''


@dataclass
class AMLModel:
    name: str = 'model'
    width: float = 100
    depth: float = 100
    height: float = 100
    unit: str = 'mm'
    drawing_title: str = ''
    drawing_subtitle: str = ''
    drawing_number: str = 'M.001.000'
    primitives: list = field(default_factory=list)

    def add(self, **kwargs):
        p = Primitive(**kwargs)

        self.primitives.append(asdict(p))

        return self

    def to_json(self, indent=2):
        return json.dumps(asdict(self), indent=indent, ensure_ascii=False)

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

        return path

    @staticmethod
    def load(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        m = AMLModel()

        for k, v in data.items():
            if k != 'primitives':
                setattr(m, k, v)

        m.primitives = data.get('primitives', [])

        return m

    @staticmethod
    def from_dict(data):
        m = AMLModel()

        for k, v in data.items():
            if k != 'primitives':
                setattr(m, k, v)

        m.primitives = data.get('primitives', [])

        return m

    @staticmethod
    def from_json(s):
        return AMLModel.from_dict(json.loads(s))

    def validate(self):
        errors = []

        for i, p in enumerate(self.primitives):
            t = p.get('type', '')

            if t not in PRIMITIVE_TYPES:
                errors.append(f'primitive[{i}]: unknown type "{t}"')

            if p.get('type') == 'logo' and not p.get('svg'):
                errors.append(f'primitive[{i}]: logo requires "svg" path')

            if p.get('type') == 'text' and not p.get('text'):
                errors.append(f'primitive[{i}]: text requires "text" value')

        return errors

    def summary(self):
        counts = {}

        for p in self.primitives:
            t = p.get('type', '?')
            counts[t] = counts.get(t, 0) + 1

        lines = [f'Model: {self.name}  ({self.width}x{self.depth}x{self.height} {self.unit})']
        lines.append(f'Primitives: {len(self.primitives)}')

        for t, n in counts.items():
            lines.append(f'  {t}: {n}')

        errors = self.validate()

        if errors:
            lines.append(f'Errors: {len(errors)}')

            for e in errors:
                lines.append(f'  ! {e}')
        
        return '\n'.join(lines)
