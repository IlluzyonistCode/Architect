import io
import sys
import traceback
from PyQt6.QtCore import QThread, pyqtSignal

class BuildWorker(QThread):
    log = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, model, out_dir, draw=True, do_step=True, do_stl=True):
        super().__init__()

        self.model = model
        self.out_dir = out_dir
        self.draw = draw
        self.do_step = do_step
        self.do_stl = do_stl

    def run(self):
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = _Relay(self.log)
        sys.stderr = _Relay(self.log)

        try:
            import os
            from architect.builder import build_aml
            from architect.exports import to_step, to_stl

            result = build_aml(
                self.model,
                output_dir=self.out_dir,
                draw=self.draw,
                exports=False
            )

            if result is None:
                self.error.emit('Build returned no geometry.')

                return

            stem = os.path.join(self.out_dir, self.model.name)
            os.makedirs(self.out_dir, exist_ok=True)

            if self.do_step:
                to_step(result, stem + '.step')

            if self.do_stl:
                to_stl(result, stem + '.stl', tolerance=0.5)

            self.finished.emit(self.out_dir)
        except Exception:
            self.error.emit(traceback.format_exc())
        finally:
            sys.stdout = old_out
            sys.stderr = old_err


class _Relay(io.TextIOBase):
    def __init__(self, sig):
        self._sig = sig

    def write(self, s):
        if s.strip():
            self._sig.emit(s.rstrip())

        return len(s)
    
    def flush(self):
        pass
