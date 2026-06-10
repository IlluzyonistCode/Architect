import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from studio.window import MainWindow

def main():
    os.environ.setdefault('ARCHITECT_MODEL', 'qwen/qwen-2.5-72b-instruct')

    app = QApplication(sys.argv)
    app.setApplicationName('Architect Studio')
    app.setOrganizationName('Architect')
    app.setStyleSheet(THEME)

    win = MainWindow()
    win.show()
    
    sys.exit(app.exec())


THEME = '''
QWidget {
    background: #0d0d0d;
    color: #f0f0f0;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
    border: none;
}
QMainWindow { background: #080808; }

QMenuBar {
    background: #111;
    border-bottom: 1px solid #222;
    padding: 2px;
    color: #ccc;
}
QMenuBar::item:selected { background: #1e1e1e; border-radius: 3px; }
QMenu {
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 4px;
    color: #ddd;
}
QMenu::item { padding: 6px 20px; border-radius: 3px; }
QMenu::item:selected { background: #252525; color: #fff; }
QMenu::separator { height: 1px; background: #222; margin: 4px 8px; }

QSplitter::handle { background: #1a1a1a; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical   { height: 1px; }

QTabWidget::pane  { border: none; background: #0d0d0d; }
QTabBar::tab {
    background: #111;
    color: #666;
    padding: 8px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 1px;
}
QTabBar::tab:selected  { color: #fff; border-bottom: 2px solid #fff; background: #0d0d0d; }
QTabBar::tab:hover     { color: #bbb; background: #161616; }

QPushButton {
    background: #181818;
    border: 1px solid #2a2a2a;
    border-radius: 5px;
    padding: 6px 14px;
    color: #ccc;
}
QPushButton:hover   { background: #202020; border-color: #3a3a3a; color: #fff; }
QPushButton:pressed { background: #0d0d0d; }
QPushButton:disabled { color: #333; border-color: #1a1a1a; }

QPushButton#primary {
    background: #e8e8e8;
    border: 1px solid #fff;
    color: #000;
    font-weight: bold;
}
QPushButton#primary:hover   { background: #fff; }
QPushButton#primary:pressed { background: #ccc; }

QPushButton#danger {
    background: #1a0a0a;
    border: 1px solid #3a1a1a;
    color: #cc4444;
}
QPushButton#danger:hover { background: #200d0d; border-color: #cc4444; }

QLineEdit, QTextEdit, QPlainTextEdit {
    background: #111;
    border: 1px solid #222;
    border-radius: 5px;
    padding: 5px 9px;
    color: #f0f0f0;
    selection-background-color: #333;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #555;
}

QComboBox {
    background: #111;
    border: 1px solid #222;
    border-radius: 5px;
    padding: 5px 9px;
    color: #f0f0f0;
    min-width: 100px;
}
QComboBox::drop-down  { border: none; width: 20px; }
QComboBox::down-arrow { image: none; }
QComboBox QAbstractItemView {
    background: #161616;
    border: 1px solid #2a2a2a;
    selection-background-color: #252525;
    color: #eee;
}

QScrollBar:vertical {
    background: #0d0d0d;
    width: 7px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #2a2a2a;
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #3a3a3a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #0d0d0d;
    height: 7px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal {
    background: #2a2a2a;
    border-radius: 3px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover { background: #3a3a3a; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QLabel           { color: #ccc; }
QLabel#title     { color: #fff; font-size: 14px; font-weight: bold; letter-spacing: 0.5px; }
QLabel#section   { color: #444; font-size: 10px; }

QGroupBox {
    border: 1px solid #1e1e1e;
    border-radius: 6px;
    margin-top: 12px;
    padding: 8px 6px 6px 6px;
    color: #555;
    font-size: 11px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #555;
}

QProgressBar {
    background: #111;
    border: 1px solid #222;
    border-radius: 3px;
    height: 5px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk { background: #fff; border-radius: 3px; }

QStatusBar {
    background: #080808;
    border-top: 1px solid #1a1a1a;
    color: #444;
    font-size: 11px;
}

QListWidget {
    background: #0d0d0d;
    border: 1px solid #1a1a1a;
    border-radius: 5px;
    outline: none;
    color: #ccc;
}
QListWidget::item         { padding: 7px 10px; border-radius: 3px; }
QListWidget::item:selected { background: #1e1e1e; color: #fff; }
QListWidget::item:hover    { background: #141414; }

QCheckBox { color: #ccc; spacing: 7px; }
QCheckBox::indicator {
    width: 15px; height: 15px;
    border: 1px solid #333;
    border-radius: 3px;
    background: #111;
}
QCheckBox::indicator:checked {
    background: #fff;
    border-color: #fff;
}

QSpinBox, QDoubleSpinBox {
    background: #111;
    border: 1px solid #222;
    border-radius: 5px;
    padding: 4px 7px;
    color: #f0f0f0;
}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background: #1a1a1a;
    border: none;
    width: 16px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: #252525;
}

QToolBar {
    background: #111;
    border-bottom: 1px solid #1a1a1a;
    spacing: 3px;
    padding: 4px 6px;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 5px 10px;
    color: #888;
}
QToolButton:hover   { background: #1a1a1a; color: #fff; border-color: #222; }
QToolButton:checked { background: #1e1e1e; color: #fff; border-color: #333; }

QHeaderView::section {
    background: #111;
    color: #555;
    padding: 5px;
    border: none;
    border-bottom: 1px solid #1e1e1e;
    font-size: 11px;
}

QTreeWidget {
    background: #0d0d0d;
    border: 1px solid #1a1a1a;
    border-radius: 5px;
    outline: none;
    color: #ccc;
}
QTreeWidget::item          { padding: 4px; }
QTreeWidget::item:selected { background: #1e1e1e; color: #fff; }

QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
'''


if __name__ == '__main__':
    main()
