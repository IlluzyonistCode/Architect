import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class LogPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.setMaximumHeight(220)
        self.setMinimumHeight(80)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        header = QWidget()
        header.setStyleSheet('background:#161616; border-top:1px solid #2a2a2a;')
        hl = QHBoxLayout(header)
        hl.setContentsMargins(10, 4, 6, 4)

        lbl = QLabel('Output')
        lbl.setStyleSheet('color:#666; font-size:11px; font-weight:bold; letter-spacing:1px;')
        btn_clear = QPushButton('Clear')
        btn_clear.setFixedSize(48, 22)
        btn_clear.setStyleSheet('font-size:10px; padding:0; background:#222; border:1px solid #333; border-radius:3px;')
        btn_clear.clicked.connect(self.clear)

        hl.addWidget(lbl)
        hl.addStretch()
        hl.addWidget(btn_clear)
        lay.addWidget(header)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont('Consolas', 11))
        self.output.setStyleSheet(
            'background:#111; color:#aaa; border:none; border-top:1px solid #1e1e1e; padding:6px;'
        )
        self.output.setMaximumBlockCount(2000)
        lay.addWidget(self.output)

    def append(self, text):
        ts = datetime.datetime.now().strftime('%H:%M:%S')

        for line in text.splitlines():
            if line.strip():
                colored = self._colorize(line)

                self.output.appendHtml(f'<span style="color:#333">[{ts}]</span> {colored}')

        self.output.verticalScrollBar().setValue(
            self.output.verticalScrollBar().maximum()
        )

    def _colorize(self, line):
        l = line.strip()

        if l.startswith('ERROR') or 'error' in l.lower() or 'Error' in l:
            return f'<span style="color:#ff6b6b">{line}</span>'

        if l.startswith('[') and '/' in l[:8]:
            return f'<span style="color:#7cb8ff">{line}</span>'

        if 'done' in l.lower() or 'complete' in l.lower() or 'saved' in l.lower() or 'OK' in l:
            return f'<span style="color:#7ec87e">{line}</span>'

        if l.startswith('AI'):
            return f'<span style="color:#c9a0ff">{line}</span>'

        if l.startswith('  ') or l.startswith('STEP') or l.startswith('STL'):
            return f'<span style="color:#888">{line}</span>'
        
        return f'<span style="color:#bbb">{line}</span>'

    def clear(self):
        self.output.clear()
