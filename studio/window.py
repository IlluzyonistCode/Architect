import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QToolBar, QStatusBar, QFileDialog,
    QMessageBox, QLabel, QProgressBar, QDialog,
    QDialogButtonBox, QCheckBox, QFormLayout
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QKeySequence
from studio.panels.primitives import PrimitivesPanel
from studio.panels.properties import PropertiesPanel
from studio.panels.viewer3d import Viewer3DPanel
from studio.panels.ai_panel import AIPanel
from studio.panels.log import LogPanel
from studio.build_worker import BuildWorker
from architect.aml import AMLModel

class BuildDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Build Options')
        self.setFixedWidth(340)

        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        f = QFormLayout()

        self.chk_step = QCheckBox('Export STEP  (.step)');  self.chk_step.setChecked(True)
        self.chk_stl = QCheckBox('Export STL   (.stl)');   self.chk_stl.setChecked(True)
        self.chk_draw = QCheckBox('Generate SVG drawing');  self.chk_draw.setChecked(False)

        f.addRow(self.chk_step)
        f.addRow(self.chk_stl)
        f.addRow(self.chk_draw)
        lay.addLayout(f)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_file = None
        self.model = None
        self.settings = QSettings('Architect', 'Studio')

        self.setWindowTitle('Architect Studio')
        self.resize(
            self.settings.value('window/width', 1440, int),
            self.settings.value('window/height', 900, int)
        )

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()
        self._connect()
        self.new_model()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.primitives_panel = PrimitivesPanel()
        self.splitter.addWidget(self.primitives_panel)

        center = QSplitter(Qt.Orientation.Vertical)
        self.viewer = Viewer3DPanel()
        self.log_panel = LogPanel()
        center.addWidget(self.viewer)
        center.addWidget(self.log_panel)
        center.setSizes([680, 180])
        self.splitter.addWidget(center)

        right = QSplitter(Qt.Orientation.Vertical)
        self.props_panel = PropertiesPanel()
        self.ai_panel = AIPanel()
        right.addWidget(self.props_panel)
        right.addWidget(self.ai_panel)
        right.setSizes([440, 380])
        self.splitter.addWidget(right)

        self.splitter.setSizes([240, 860, 340])
        root.addWidget(self.splitter)

    def _build_menu(self):
        mb = self.menuBar()

        fm = mb.addMenu('File')
        fm.addAction(self._a('New', self.new_model, 'Ctrl+N'))
        fm.addAction(self._a('Open…', self.open_file, 'Ctrl+O'))
        fm.addSeparator()
        fm.addAction(self._a('Save', self.save_file, 'Ctrl+S'))
        fm.addAction(self._a('Save As…', self.save_file_as, 'Ctrl+Shift+S'))
        fm.addSeparator()
        fm.addAction(self._a('Quit', self.close, 'Ctrl+Q'))

        bm = mb.addMenu('Build')
        bm.addAction(self._a('Build…', self.build_model, 'F5'))
        bm.addAction(self._a('Quick STEP+STL', self.quick_export, 'F6'))
        bm.addSeparator()
        bm.addAction(self._a('Validate', self.validate, 'F7'))

        vm = mb.addMenu('View')
        vm.addAction(self._a('Reset Layout', self.reset_layout))

        hm = mb.addMenu('Help')
        hm.addAction(self._a('Logo Placement Guide', self.logo_guide))
        hm.addSeparator()
        hm.addAction(self._a('About', self.about))

    def _build_toolbar(self):
        tb = QToolBar('Main')
        tb.setMovable(False)
        self.addToolBar(tb)

        for text, slot, tip in [
            ('⬜  New', self.new_model, 'New model (Ctrl+N)'),
            ('📂  Open', self.open_file, 'Open .aml.json (Ctrl+O)'),
            ('💾  Save', self.save_file, 'Save (Ctrl+S)'),
            (None, None, None),
            ('⚙  Build', self.build_model, 'Build STEP+STL (F5)'),
            ('▶  STEP+STL', self.quick_export, 'Quick export without drawing (F6)'),
            ('✔  Validate', self.validate, 'Validate model (F7)')
        ]:
            if text is None:
                tb.addSeparator()

            else:
                a = QAction(text, self)
                a.triggered.connect(slot)
                a.setToolTip(tip)
                tb.addAction(a)

    def _build_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.status_label = QLabel('Ready')
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(160)
        self.progress.setRange(0, 0)
        self.progress.hide()
        sb.addWidget(self.status_label)
        sb.addPermanentWidget(self.progress)

    def _connect(self):
        self.primitives_panel.primitive_added.connect(self._on_prim_added)
        self.primitives_panel.primitive_selected.connect(self._on_prim_selected_from_list)
        self.props_panel.primitive_changed.connect(self._on_prim_changed)
        self.ai_panel.model_generated.connect(self._on_ai_model)
        self.ai_panel.log_message.connect(self.log_panel.append)

        self.viewer.primitive_selected.connect(self._on_prim_selected_from_viewer)
        self.viewer.primitive_changed.connect(self._on_prim_moved_in_viewer)

    def _a(self, text, slot=None, shortcut=None):
        a = QAction(text, self)

        if slot:
            a.triggered.connect(slot)

        if shortcut:
            a.setShortcut(QKeySequence(shortcut))

        return a

    def new_model(self):
        self.model = AMLModel()
        self.model.name = 'new_model'
        self.current_file = None
        self.setWindowTitle('Architect Studio — new_model')
        self.primitives_panel.load_model(self.model)
        self.viewer.load_model(self.model)
        self.log_panel.append('New model created.')

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Open AML Model', '',
            'ArchitectML (*.aml.json *.json);;All Files (*)'
        )

        if not path:
            return

        try:
            self.model = AMLModel.load(path)
            self.current_file = path
            self.setWindowTitle(f'Architect Studio — {os.path.basename(path)}')
            self.primitives_panel.load_model(self.model)
            self.viewer.load_model(self.model)
            self.ai_panel.set_model(self.model)
            self.log_panel.append(f'Opened: {path}')
        except Exception as e:
            QMessageBox.critical(self, 'Open Error', str(e))

    def save_file(self):
        if not self.current_file:
            self.save_file_as()

        else:
            self._do_save(self.current_file)

    def save_file_as(self):
        name = getattr(self.model, 'name', 'model') if self.model else 'model'
        path, _ = QFileDialog.getSaveFileName(
            self, 'Save AML Model', f'{name}.aml.json',
            'ArchitectML (*.aml.json);;All Files (*)'
        )

        if path:
            self.current_file = path
            self._do_save(path)

    def _do_save(self, path):
        try:
            self.model.save(path)
            self.setWindowTitle(f'Architect Studio — {os.path.basename(path)}')
            self.status_label.setText(f'Saved: {os.path.basename(path)}')
            self.log_panel.append(f'Saved: {path}')
        except Exception as e:
            QMessageBox.critical(self, 'Save Error', str(e))

    def build_model(self):
        if not self.model:
            return

        dlg = BuildDialog(self)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        out_dir = QFileDialog.getExistingDirectory(self, 'Select Output Folder')

        if not out_dir:
            return

        self._run_build(out_dir,
                        draw=dlg.chk_draw.isChecked(),
                        step=dlg.chk_step.isChecked(),
                        stl=dlg.chk_stl.isChecked())

    def quick_export(self):
        if not self.model:
            return

        out_dir = QFileDialog.getExistingDirectory(self, 'Select Output Folder')

        if not out_dir:
            return

        self._run_build(out_dir, draw=False, step=True, stl=True)

    def _run_build(self, out_dir, draw=False, step=True, stl=True):
        self.progress.show()
        self.status_label.setText('Building…')
        self.log_panel.append(f'\nBuilding → {out_dir}')

        self.worker = BuildWorker(self.model, out_dir, draw=draw,
                                  do_step=step, do_stl=stl)
        self.worker.log.connect(self.log_panel.append)
        self.worker.finished.connect(self._on_build_done)
        self.worker.error.connect(self._on_build_error)
        self.worker.start()

    def _on_build_done(self, out_dir):
        self.progress.hide()
        self.status_label.setText(f'Done → {out_dir}')
        self.log_panel.append(f'Build complete: {out_dir}')

        QMessageBox.information(self, 'Build Complete', f'Files saved to:\n{out_dir}')

    def _on_build_error(self, msg):
        self.progress.hide()
        self.status_label.setText('Build failed.')
        self.log_panel.append(f'\nERROR: {msg}')

        QMessageBox.critical(self, 'Build Error', msg)

    def _on_prim_added(self, prim_dict):
        self.model.primitives.append(prim_dict)
        self.viewer.load_model(self.model)

    def _on_prim_selected_from_list(self, index, prim_dict):
        self.props_panel.load_primitive(index, prim_dict)
        self.viewer.select(index)

    def _on_prim_selected_from_viewer(self, index, prim_dict):
        self.props_panel.load_primitive(index, prim_dict)
        self.primitives_panel.list.setCurrentRow(index)
        self.status_label.setText(
            f'Selected: [{index}] {prim_dict.get("label") or prim_dict.get("type")}  '
            f'· ←→↑↓ move  · Shift+↑↓ move Z  · [ ] resize'
        )

    def _on_prim_moved_in_viewer(self, index, prim_dict):
        if 0 <= index < len(self.model.primitives):
            self.model.primitives[index] = prim_dict
            self.props_panel.load_primitive(index, prim_dict)

            p = prim_dict

            self.status_label.setText(
                f'[{index}] {p.get("label") or p.get("type")}  '
                f'x={p.get("x",0):.1f}  y={p.get("y",0):.1f}  z={p.get("z",0):.1f}'
            )

    def _on_prim_changed(self, index, prim_dict):
        if 0 <= index < len(self.model.primitives):
            self.model.primitives[index] = prim_dict
            self.viewer.gl.update()

    def _on_ai_model(self, model):
        self.model = model
        self.current_file = None
        self.setWindowTitle(f'Architect Studio — {model.name} [AI]')
        self.primitives_panel.load_model(model)
        self.viewer.load_model(model)
        self.ai_panel.set_model(model)
        self.log_panel.append(f'AI model loaded: {model.name} ({len(model.primitives)} primitives)')

    def validate(self):
        if not self.model:
            return

        errors = self.model.validate()

        if not errors:
            QMessageBox.information(self, 'Validate', 'No errors found.')

            self.log_panel.append('Validate: OK')

        else:
            QMessageBox.warning(self, 'Validate', '\n'.join(errors))

            self.log_panel.append('Validate errors:\n' + '\n'.join(errors))

    def reset_layout(self):
        self.splitter.setSizes([240, 860, 340])

    def logo_guide(self):
        QMessageBox.information(self, 'Logo Placement Guide',
            'How to place a logo on a wall:\n\n'
            '1. Add primitive → Logo\n'
            '2. SVG: browse to your .svg file\n'
            '3. Width/Height: size of the logo (mm)\n'
            '4. Extrude depth: how much it protrudes\n'
            '5. Use Wall Preset buttons:\n'
            '   Front wall  → rotate_x = 90\n'
            '   Back wall   → rotate_x = -90\n'
            '   Left wall   → rotate_x = 90, rotate_z = 90\n'
            '   Right wall  → rotate_x = 90, rotate_z = -90\n'
            '   Top surface → no rotation\n'
            '6. X/Y/Z: position on that surface\n\n'
            'AI prompt example:\n'
            '"Add logo.svg on the front wall centered at x=0, z=280, size 35mm, depth 3mm"'
        )

    def about(self):
        QMessageBox.about(self, 'Architect Studio',
            'Architect Studio\n\n'
            'AI-powered 3D model platform\n'
            'OpenRouter · build123d · PyQt6\n\n'
            'Exports: STEP · STL · SVG drawing')

    def closeEvent(self, e):
        self.settings.setValue('window/width', self.width())
        self.settings.setValue('window/height', self.height())

        e.accept()
