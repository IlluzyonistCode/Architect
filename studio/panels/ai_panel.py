import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QLineEdit, QFileDialog,
    QComboBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import pyqtSignal, QThread, Qt

MODELS = [
    'qwen/qwen-2.5-72b-instruct',
    'google/gemini-2.0-flash-001',
    'anthropic/claude-3.5-sonnet',
    'meta-llama/llama-3.3-70b-instruct',
    'openai/gpt-4o',
    'mistralai/mistral-large'
]


class AIWorker(QThread):
    done = pyqtSignal(object)
    error = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, mode, prompt, image_path, pdf_path, api_key, model, existing_model, feedback):
        super().__init__()
        self.mode = mode
        self.prompt = prompt
        self.image_path = image_path
        self.pdf_path = pdf_path
        self.api_key = api_key
        self.model = model
        self.existing_model = existing_model
        self.feedback = feedback

    def run(self):
        try:
            import architect.ai as ai

            key = self.api_key or os.environ.get('OPENROUTER_API_KEY', '')

            if self.mode == 'text':
                self.log.emit(f'AI: generating from text [{self.model}]...')

                result = ai.from_text(self.prompt, api_key=key, model=self.model)

            elif self.mode == 'image':
                self.log.emit(f'AI: reading image [{self.model}]...')

                result = ai.from_image(self.image_path, prompt=self.prompt, api_key=key, model=self.model)

            elif self.mode == 'pdf':
                self.log.emit(f'AI: reading PDF [{self.model}]...')

                result = ai.from_pdf(self.pdf_path, prompt=self.prompt, api_key=key, model=self.model)

            elif self.mode == 'refine':
                self.log.emit(f'AI: refining model [{self.model}]...')

                result = ai.refine(self.existing_model, self.feedback, api_key=key, ai_model=self.model)

            self.log.emit(f'AI: done — {len(result.primitives)} primitives.')
            self.done.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AIPanel(QWidget):
    model_generated = pyqtSignal(object)
    log_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setMinimumWidth(280)
        self._current_model = None
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        title = QLabel('AI Generator')
        title.setObjectName('title')
        lay.addWidget(title)

        g = QGroupBox('OpenRouter')
        f = QFormLayout(g)
        f.setSpacing(5)

        self.w_key = QLineEdit()
        self.w_key.setPlaceholderText('sk-or-v1-... (or set OPENROUTER_API_KEY)')
        self.w_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.w_key.setText(os.environ.get('OPENROUTER_API_KEY', ''))

        self.w_model = QComboBox()
        self.w_model.addItems(MODELS)
        self.w_model.setEditable(True)

        f.addRow('API Key', self.w_key)
        f.addRow('Model', self.w_model)
        lay.addWidget(g)

        g2 = QGroupBox('From Description')
        v2 = QVBoxLayout(g2)
        v2.setSpacing(5)

        self.w_prompt = QTextEdit()
        self.w_prompt.setPlaceholderText(
            'Describe your model...\n\n'
            'Example: Exhibition stand 350x200x300mm, '
            '4 corner pipe columns radius 2.5mm, '
            'flat roof 40mm thick, 2 logos on front.'
        )
        self.w_prompt.setMinimumHeight(90)
        self.w_prompt.setMaximumHeight(130)
        self.btn_generate = QPushButton('✨  Generate from Text')
        self.btn_generate.setObjectName('primary')
        self.btn_generate.clicked.connect(self._gen_text)
        v2.addWidget(self.w_prompt)
        v2.addWidget(self.btn_generate)
        lay.addWidget(g2)

        g3 = QGroupBox('From Sketch / PDF')
        v3 = QVBoxLayout(g3)
        v3.setSpacing(5)

        img_row = QWidget()
        il = QHBoxLayout(img_row)
        il.setContentsMargins(0,0,0,0)
        self.w_image = QLineEdit()
        self.w_image.setPlaceholderText('sketch.png / .jpg / .webp')
        btn_img = QPushButton('…')
        btn_img.setFixedWidth(28)
        btn_img.clicked.connect(self._pick_image)
        il.addWidget(self.w_image)
        il.addWidget(btn_img)

        pdf_row = QWidget()
        pl = QHBoxLayout(pdf_row)
        pl.setContentsMargins(0,0,0,0)
        self.w_pdf = QLineEdit()
        self.w_pdf.setPlaceholderText('drawing.pdf')
        btn_pdf = QPushButton('…')
        btn_pdf.setFixedWidth(28)
        btn_pdf.clicked.connect(self._pick_pdf)
        pl.addWidget(self.w_pdf)
        pl.addWidget(btn_pdf)

        btn_row = QWidget()
        br = QHBoxLayout(btn_row)
        br.setContentsMargins(0,0,0,0)
        br.setSpacing(6)
        self.btn_from_img = QPushButton('🖼  From Image')
        self.btn_from_pdf = QPushButton('📄  From PDF')
        self.btn_from_img.clicked.connect(self._gen_image)
        self.btn_from_pdf.clicked.connect(self._gen_pdf)
        br.addWidget(self.btn_from_img)
        br.addWidget(self.btn_from_pdf)

        v3.addWidget(QLabel('Image:'))
        v3.addWidget(img_row)
        v3.addWidget(QLabel('PDF:'))
        v3.addWidget(pdf_row)
        v3.addWidget(btn_row)
        lay.addWidget(g3)

        g4 = QGroupBox('Refine Current Model')
        v4 = QVBoxLayout(g4)
        v4.setSpacing(5)
        self.w_refine = QLineEdit()
        self.w_refine.setPlaceholderText('Add a window 80x60mm on the left panel...')
        self.btn_refine = QPushButton('🔧  Refine')
        self.btn_refine.clicked.connect(self._gen_refine)
        v4.addWidget(self.w_refine)
        v4.addWidget(self.btn_refine)
        lay.addWidget(g4)
        lay.addStretch()

    def _pick_image(self):
        p, _ = QFileDialog.getOpenFileName(self, 'Select Image', '', 'Images (*.png *.jpg *.jpeg *.webp)')

        if p: self.w_image.setText(p)

    def _pick_pdf(self):
        p, _ = QFileDialog.getOpenFileName(self, 'Select PDF', '', 'PDF (*.pdf)')

        if p: self.w_pdf.setText(p)

    def _key(self):
        return self.w_key.text().strip()

    def _mdl(self):
        return self.w_model.currentText().strip()

    def _set_busy(self, busy):
        for b in [self.btn_generate, self.btn_from_img, self.btn_from_pdf, self.btn_refine]:
            b.setEnabled(not busy)

    def _gen_text(self):
        prompt = self.w_prompt.toPlainText().strip()

        if not prompt:
            return

        self._run('text', prompt=prompt)

    def _gen_image(self):
        path = self.w_image.text().strip()

        if not path:
            return

        prompt = self.w_prompt.toPlainText().strip() or 'Generate a 3D model from this sketch.'

        self._run('image', prompt=prompt, image_path=path)

    def _gen_pdf(self):
        path = self.w_pdf.text().strip()

        if not path:
            return

        prompt = self.w_prompt.toPlainText().strip() or 'Generate a 3D model from this technical drawing.'

        self._run('pdf', prompt=prompt, pdf_path=path)

    def _gen_refine(self):
        feedback = self.w_refine.text().strip()

        if not feedback or not self._current_model:
            return

        self._run('refine', feedback=feedback)

    def _run(self, mode, prompt='', image_path='', pdf_path='', feedback=''):
        self._set_busy(True)
        self.log_message.emit(f'AI starting [{mode}]...')
        self.worker = AIWorker(
            mode, prompt, image_path, pdf_path,
            self._key(), self._mdl(), self._current_model, feedback
        )
        self.worker.done.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        self.worker.log.connect(self.log_message)
        self.worker.start()

    def _on_done(self, model):
        self._set_busy(False)
        self._current_model = model
        self.model_generated.emit(model)

    def _on_error(self, msg):
        self._set_busy(False)
        self.log_message.emit(f'AI ERROR: {msg}')

    def set_model(self, model):
        self._current_model = model
