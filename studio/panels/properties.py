import importlib.util as _ilu
import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QDoubleSpinBox, QCheckBox, QComboBox,
    QGroupBox, QScrollArea, QPushButton, QFileDialog,
    QHBoxLayout, QSpinBox
)
from PyQt6.QtCore import pyqtSignal, Qt

_aml_path = os.path.join(os.path.dirname(__file__), '..', '..', 'architect')
_spec = _ilu.spec_from_file_location('architect.aml', os.path.join(_aml_path, 'aml.py'))
_aml = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_aml)

PRIMITIVE_TYPES = _aml.PRIMITIVE_TYPES

FACES = ['top', 'front', 'back', 'left', 'right', 'bottom']

LOGO_HINT = (
    'Logo is extruded along Z-axis.\n'
    'For a FRONT wall: set rotate_x = 90\n'
    'For a LEFT wall: set rotate_x = 90, rotate_z = 90\n'
    'Use x/y/z to position on the surface.\n'
    'Each logo gets a fresh SVG import — no OCCT hangs.'
)


class PropertiesPanel(QScrollArea):
    primitive_changed = pyqtSignal(int, dict)

    def __init__(self):
        super().__init__()

        self.setWidgetResizable(True)
        self.setMinimumWidth(270)
        self._index = -1
        self._block = False

        inner = QWidget()
        self.setWidget(inner)
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel('Properties')
        title.setObjectName('title')
        lay.addWidget(title)

        self._empty = QLabel('Select a primitive\nto edit its properties.')
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setStyleSheet('color: #333; font-size: 12px; padding: 30px;')
        lay.addWidget(self._empty)

        self._form = QWidget()
        self._form.hide()
        lay.addWidget(self._form)
        self._build_form()

    def _build_form(self):
        lay = QVBoxLayout(self._form)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        g = QGroupBox('Identity')
        f = QFormLayout(g); f.setSpacing(5)
        self.w_label = QLineEdit()
        self.w_type = QComboBox()
        self.w_type.addItems(sorted(PRIMITIVE_TYPES))
        f.addRow('Label', self.w_label)
        f.addRow('Type', self.w_type)
        lay.addWidget(g)

        g2 = QGroupBox('Position (mm)')
        f2 = QFormLayout(g2); f2.setSpacing(5)
        self.w_x = self._dspin(-9999, 9999)
        self.w_y = self._dspin(-9999, 9999)
        self.w_z = self._dspin(-9999, 9999)
        f2.addRow('X', self.w_x)
        f2.addRow('Y', self.w_y)
        f2.addRow('Z', self.w_z)
        lay.addWidget(g2)

        g3 = QGroupBox('Size (mm)')
        f3 = QFormLayout(g3); f3.setSpacing(5)
        self.w_w = self._dspin(0, 9999)
        self.w_d = self._dspin(0, 9999)
        self.w_h = self._dspin(0, 9999)
        self.w_radius = self._dspin(0, 9999)
        self.w_depth = self._dspin(0, 9999)
        f3.addRow('Width', self.w_w)
        f3.addRow('Depth (Y)', self.w_d)
        f3.addRow('Height (Z)', self.w_h)
        f3.addRow('Radius', self.w_radius)
        f3.addRow('Extrude depth', self.w_depth)
        lay.addWidget(g3)

        g4 = QGroupBox('Rotation (deg)')
        f4 = QFormLayout(g4); f4.setSpacing(5)
        self.w_rx = self._dspin(-360, 360)
        self.w_ry = self._dspin(-360, 360)
        self.w_rz = self._dspin(-360, 360)
        f4.addRow('Rotate X', self.w_rx)
        f4.addRow('Rotate Y', self.w_ry)
        f4.addRow('Rotate Z', self.w_rz)
        lay.addWidget(g4)

        g5 = QGroupBox('Orientation')
        f5 = QFormLayout(g5); f5.setSpacing(5)
        self.w_face = QComboBox()
        self.w_face.addItems(FACES)
        f5.addRow('Face normal', self.w_face)
        lay.addWidget(g5)

        self.g_logo = QGroupBox('Logo / SVG')
        v_logo = QVBoxLayout(self.g_logo)
        v_logo.setSpacing(6)

        hint = QLabel(LOGO_HINT)
        hint.setWordWrap(True)
        hint.setStyleSheet('color:#444; font-size:11px; padding:4px;')
        v_logo.addWidget(hint)

        row_svg = QWidget()
        rl = QHBoxLayout(row_svg); rl.setContentsMargins(0,0,0,0); rl.setSpacing(4)
        self.w_svg = QLineEdit()
        self.w_svg.setPlaceholderText('logo.svg')
        btn_svg = QPushButton('…')
        btn_svg.setFixedWidth(28)
        btn_svg.clicked.connect(self._pick_svg)
        rl.addWidget(self.w_svg)
        rl.addWidget(btn_svg)

        preset_row = QWidget()
        pl = QHBoxLayout(preset_row); pl.setContentsMargins(0,0,0,0); pl.setSpacing(4)

        for label, rx, ry, rz in [
            ('Front', 90, 0, 0),
            ('Back', -90, 0, 0),
            ('Left', 90, 0, 90),
            ('Right', 90, 0,-90),
            ('Top', 0, 0, 0)
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.setStyleSheet('font-size:10px; padding:0 6px;')
            btn.clicked.connect(lambda _, a=rx, b=ry, c=rz: self._preset_rot(a, b, c))
            pl.addWidget(btn)

        v_logo.addWidget(QLabel('SVG file:'))
        v_logo.addWidget(row_svg)
        v_logo.addWidget(QLabel('Wall preset:'))
        v_logo.addWidget(preset_row)
        lay.addWidget(self.g_logo)

        g6 = QGroupBox('Text / Grid content')
        f6 = QFormLayout(g6); f6.setSpacing(5)
        self.w_text = QLineEdit()
        self.w_font_size = self._dspin(1, 500)
        self.w_rows = self._ispin(1, 50)
        self.w_cols = self._ispin(1, 50)
        self.w_spacing = self._dspin(0, 500)
        f6.addRow('Text', self.w_text)
        f6.addRow('Font size', self.w_font_size)
        f6.addRow('Rows', self.w_rows)
        f6.addRow('Cols', self.w_cols)
        f6.addRow('Spacing', self.w_spacing)
        lay.addWidget(g6)

        g7 = QGroupBox('Flags')
        f7 = QFormLayout(g7); f7.setSpacing(5)
        self.w_subtract = QCheckBox('Subtract  (boolean cut from model)')
        f7.addRow(self.w_subtract)
        lay.addWidget(g7)

        for w in [self.w_x, self.w_y, self.w_z, self.w_w, self.w_d, self.w_h,
                  self.w_radius, self.w_depth, self.w_rx, self.w_ry, self.w_rz,
                  self.w_font_size, self.w_spacing]:
            w.valueChanged.connect(self._emit)

        for w in [self.w_rows, self.w_cols]:
            w.valueChanged.connect(self._emit)

        self.w_label.textChanged.connect(self._emit)
        self.w_type.currentTextChanged.connect(self._on_type_changed)
        self.w_face.currentTextChanged.connect(self._emit)
        self.w_svg.textChanged.connect(self._emit)
        self.w_text.textChanged.connect(self._emit)
        self.w_subtract.stateChanged.connect(self._emit)

    def _dspin(self, lo, hi):
        s = QDoubleSpinBox()
        s.setRange(lo, hi)
        s.setDecimals(1)
        s.setSingleStep(1.0)
        s.setMinimumWidth(90)

        return s

    def _ispin(self, lo, hi):
        s = QSpinBox()
        s.setRange(lo, hi)
        s.setMinimumWidth(90)

        return s

    def _pick_svg(self):
        p, _ = QFileDialog.getOpenFileName(self, 'Select SVG Logo', '', 'SVG (*.svg);;All Files (*)')

        if p:
            self.w_svg.setText(p)

    def _preset_rot(self, rx, ry, rz):
        self._block = True
        self.w_rx.setValue(rx)
        self.w_ry.setValue(ry)
        self.w_rz.setValue(rz)
        self._block = False
        self._emit()

    def _on_type_changed(self, t):
        self.g_logo.setVisible(t == 'logo')
        self._emit()

    def load_primitive(self, index, p):
        self._block = True
        self._index = index
        self._empty.hide()
        self._form.show()

        self.w_label.setText(p.get('label', ''))
        self.w_type.setCurrentText(p.get('type', 'box'))
        self.w_x.setValue(p.get('x', 0))
        self.w_y.setValue(p.get('y', 0))
        self.w_z.setValue(p.get('z', 0))
        self.w_w.setValue(p.get('w', 10))
        self.w_d.setValue(p.get('d', 10))
        self.w_h.setValue(p.get('h', 10))
        self.w_radius.setValue(p.get('radius', 5))
        self.w_depth.setValue(p.get('depth', 2))
        self.w_rx.setValue(p.get('rotate_x', 0))
        self.w_ry.setValue(p.get('rotate_y', 0))
        self.w_rz.setValue(p.get('rotate_z', 0))
        self.w_face.setCurrentText(p.get('face', 'top'))
        self.w_svg.setText(p.get('svg', ''))
        self.w_text.setText(p.get('text', ''))
        self.w_font_size.setValue(p.get('font_size', 8))
        self.w_rows.setValue(int(p.get('rows', 3)))
        self.w_cols.setValue(int(p.get('cols', 3)))
        self.w_spacing.setValue(p.get('spacing', 5))
        self.w_subtract.setChecked(bool(p.get('subtract', False)))

        self.g_logo.setVisible(p.get('type') == 'logo')
        self._block = False

    def _emit(self, *_):
        if self._block or self._index < 0:
            return

        self.primitive_changed.emit(self._index, self._collect())

    def _collect(self):
        return {
            'type': self.w_type.currentText(),
            'label': self.w_label.text(),
            'x': self.w_x.value(),
            'y': self.w_y.value(),
            'z': self.w_z.value(),
            'w': self.w_w.value(),
            'd': self.w_d.value(),
            'h': self.w_h.value(),
            'radius': self.w_radius.value(),
            'depth': self.w_depth.value(),
            'rotate_x': self.w_rx.value(),
            'rotate_y': self.w_ry.value(),
            'rotate_z': self.w_rz.value(),
            'face': self.w_face.currentText(),
            'svg': self.w_svg.text(),
            'text': self.w_text.text(),
            'font_size': self.w_font_size.value(),
            'rows': self.w_rows.value(),
            'cols': self.w_cols.value(),
            'spacing': self.w_spacing.value(),
            'subtract': self.w_subtract.isChecked()
        }
