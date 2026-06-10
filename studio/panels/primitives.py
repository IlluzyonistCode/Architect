import importlib.util as _ilu
import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QMenu
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from dataclasses import asdict

_aml_path = os.path.join(os.path.dirname(__file__), '..', '..', 'architect')

sys.path.insert(0, os.path.abspath(_aml_path))

_spec = _ilu.spec_from_file_location('architect.aml', os.path.join(_aml_path, 'aml.py'))
_aml = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_aml)

Primitive = _aml.Primitive
PRIMITIVE_TYPES_LOCAL = _aml.PRIMITIVE_TYPES


TYPES = [
    ('📦', 'box', 'Box'),
    ('🔵', 'cylinder', 'Cylinder'),
    ('⭕', 'pipe', 'Pipe'),
    ('🟤', 'sphere', 'Sphere'),
    ('🟩', 'panel', 'Panel'),
    ('🏠', 'roof', 'Roof'),
    ('🌉', 'arch', 'Arch'),
    ('⊞', 'grid', 'Grid'),
    ('🖼', 'logo', 'Logo'),
    ('🔤', 'text', 'Text')
]

TYPE_ICONS = {t: ico for ico, t, _ in TYPES}


class PrimitivesPanel(QWidget):
    primitive_added = pyqtSignal(dict)
    primitive_selected = pyqtSignal(int, dict)

    def __init__(self):
        super().__init__()

        self.setMinimumWidth(220)
        self.setMaximumWidth(320)
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        title = QLabel('Primitives')
        title.setObjectName('title')
        lay.addWidget(title)

        grid = QWidget()
        gl = QHBoxLayout(grid)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.setSpacing(4)

        self.add_btn = QPushButton('＋ Add')
        self.add_btn.setObjectName('primary')
        self.add_btn.clicked.connect(self._show_add_menu)

        self.del_btn = QPushButton('✕')
        self.del_btn.setObjectName('danger')
        self.del_btn.setFixedWidth(36)
        self.del_btn.clicked.connect(self._delete_selected)

        self.up_btn = QPushButton('↑')
        self.up_btn.setFixedWidth(36)
        self.up_btn.clicked.connect(self._move_up)

        self.down_btn = QPushButton('↓')
        self.down_btn.setFixedWidth(36)
        self.down_btn.clicked.connect(self._move_down)

        gl.addWidget(self.add_btn)
        gl.addWidget(self.up_btn)
        gl.addWidget(self.down_btn)
        gl.addWidget(self.del_btn)
        lay.addWidget(grid)

        self.list = QListWidget()
        self.list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list.currentRowChanged.connect(self._on_select)
        lay.addWidget(self.list)

    def _show_add_menu(self):
        menu = QMenu(self)

        for ico, t, label in TYPES:
            menu.addAction(f'{ico}  {label}', lambda t=t: self._add(t))

        menu.exec(self.add_btn.mapToGlobal(self.add_btn.rect().bottomLeft()))

    def _add(self, prim_type):
        p = asdict(Primitive(type=prim_type, label=prim_type))

        self._append_item(p)
        self.primitive_added.emit(p)

    def _append_item(self, p):
        ico = TYPE_ICONS.get(p['type'], '◈')
        label = p.get('label') or p['type']
        item = QListWidgetItem(f'{ico}  {label}')
        item.setData(Qt.ItemDataRole.UserRole, p)

        self.list.addItem(item)
        self.list.setCurrentItem(item)

    def _on_select(self, row):
        if row < 0:
            return

        item = self.list.item(row)

        if item:
            self.primitive_selected.emit(row, item.data(Qt.ItemDataRole.UserRole))

    def _delete_selected(self):
        row = self.list.currentRow()

        if row >= 0:
            self.list.takeItem(row)

    def _move_up(self):
        row = self.list.currentRow()

        if row > 0:
            item = self.list.takeItem(row)

            self.list.insertItem(row - 1, item)
            self.list.setCurrentRow(row - 1)

    def _move_down(self):
        row = self.list.currentRow()

        if row < self.list.count() - 1:
            item = self.list.takeItem(row)

            self.list.insertItem(row + 1, item)
            self.list.setCurrentRow(row + 1)

    def load_model(self, model):
        self.list.clear()

        for p in model.primitives:
            self._append_item(p)

    def update_item(self, row, p):
        item = self.list.item(row)

        if item:
            ico = TYPE_ICONS.get(p['type'], '◈')
            label = p.get('label') or p['type']
            item.setText(f'{ico}  {label}')
            item.setData(Qt.ItemDataRole.UserRole, p)
