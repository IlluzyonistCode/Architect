import math
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget
)
from OpenGL.GL import *
from OpenGL.GLU import *

PALETTE = [
    (0.27, 0.53, 0.80),
    (0.27, 0.67, 0.80),
    (0.24, 0.75, 0.63),
    (0.49, 0.75, 0.27),
    (0.80, 0.53, 0.27),
    (0.80, 0.27, 0.53),
    (0.53, 0.27, 0.80),
    (0.27, 0.80, 0.53),
    (0.33, 0.47, 0.93),
    (0.93, 0.47, 0.33)
]

MOVE_STEP = 5.0
RESIZE_STEP = 5.0

VIEWS = {
    'iso': (35, 45, 'Iso'),
    'front': (90, 0, 'Front'),
    'back': (90, 180, 'Back'),
    'left': (90, 270, 'Left'),
    'right': (90, 90, 'Right'),
    'top': (0, 0, 'Top'),
    'bottom': (180, 0, 'Bottom')
}

NUMPAD_VIEWS = [
    (Qt.Key.Key_0, 'iso'),
    (Qt.Key.Key_1, 'front'),
    (Qt.Key.Key_3, 'right'),
    (Qt.Key.Key_4, 'left'),
    (Qt.Key.Key_5, 'iso'),
    (Qt.Key.Key_6, 'right'),
    (Qt.Key.Key_7, 'top'),
    (Qt.Key.Key_9, 'bottom')
]

_BOX_TYPES = {'box', 'panel', 'roof', 'logo', 'text', 'slot', 'keyway', 'grid'}
_RADIAL_TYPES = {'cylinder', 'pipe', 'cone', 'sphere', 'torus', 'spring', 'thread', 'gear'}


class GLViewer(QOpenGLWidget):
    primitive_selected = pyqtSignal(int, dict)
    primitive_changed = pyqtSignal(int, dict)

    def __init__(self):
        super().__init__()

        self.model = None
        self.selected = -1

        self.rot_x = 35.0
        self.rot_z = 45.0
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0

        self._last = QPoint()
        self._rmb = False
        self._drag = False

        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def load_model(self, model):
        self.model = model
        self.selected = -1
        self.update()

    def select(self, index):
        self.selected = index
        self.update()

    def set_view(self, name):
        rx, rz, _ = VIEWS.get(name, VIEWS['iso'])

        self.rot_x = float(rx)
        self.rot_z = float(rz)
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.update()

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_NORMALIZE)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)

        glLightfv(GL_LIGHT0, GL_POSITION, [ 1.0, -1.0, 1.5, 0.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.85, 0.85, 0.85, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.18, 0.18, 0.20, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.30, 0.30, 0.30, 1.0])

        glLightfv(GL_LIGHT1, GL_POSITION, [-1.0, 1.0, 0.5, 0.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.22, 0.28, 0.42, 1.0])
        glLightfv(GL_LIGHT1, GL_AMBIENT, [0.00, 0.00, 0.00, 1.0])

        glClearColor(0.07, 0.07, 0.07, 1.0)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, max(h, 1))

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, self.width() / max(self.height(), 1), 0.5, 80000.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        sz = self._scene_size()
        dist = sz * 2.5 / self.zoom
        cx, cy, cz = self._scene_center()

        gluLookAt(
            cx + dist * 0.6, cy - dist * 0.8, cz + dist * 0.7,
            cx, cy, cz,
            0, 0, 1
        )

        glTranslatef(self.pan_x, self.pan_y, 0)
        glTranslatef(cx, cy, cz)
        glRotatef(self.rot_x, 1, 0, 0)
        glRotatef(self.rot_z, 0, 0, 1)
        glTranslatef(-cx, -cy, -cz)

        self._draw_grid()
        self._draw_axes(sz)

        if self.model:
            self._draw_all_primitives()

    def _scene_center(self):
        if not self.model or not self.model.primitives:
            return 0.0, 0.0, 50.0

        return 0.0, 0.0, self.model.height / 2

    def _scene_size(self):
        if not self.model:
            return 300.0

        return max(self.model.width, self.model.depth, self.model.height, 100.0)

    def _draw_grid(self):
        sz = self._scene_size() * 1.5
        step = max(10, int(sz / 20) // 10 * 10)
        n = int(sz / step)

        glDisable(GL_LIGHTING)
        glLineWidth(1.0)
        glBegin(GL_LINES)

        for i in range(-n, n + 1):
            t = i * step
            v = 0.22 if i == 0 else 0.15

            glColor3f(v, v, v)
            glVertex3f(t, -n * step, 0)
            glVertex3f(t, n * step, 0)
            glVertex3f(-n * step, t, 0)
            glVertex3f(n * step, t, 0)

        glEnd()
        glEnable(GL_LIGHTING)

    def _draw_axes(self, sz):
        s = sz * 0.15

        glDisable(GL_LIGHTING)
        glLineWidth(2.5)
        glBegin(GL_LINES)

        glColor3f(0.9, 0.2, 0.2)
        glVertex3f(0, 0, 0)
        glVertex3f(s, 0, 0)

        glColor3f(0.2, 0.8, 0.2)
        glVertex3f(0, 0, 0)
        glVertex3f(0, s, 0)

        glColor3f(0.2, 0.4, 0.9)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, s)

        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)

    def _draw_all_primitives(self):
        for i, prim in enumerate(self.model.primitives):
            self._draw_primitive(i, prim, selected=(i == self.selected))

    def _draw_primitive(self, index, prim, selected):
        ptype = prim.get('type', 'box')

        x, y, z = prim.get('x', 0), prim.get('y', 0), prim.get('z', 0)
        w, d, h = prim.get('w', 10), prim.get('d', 10), prim.get('h', 10)
        r = prim.get('radius', 5)
        r2 = prim.get('radius2', 2)
        depth = prim.get('depth', 2)
        rx, ry, rz = prim.get('rotate_x', 0), prim.get('rotate_y', 0), prim.get('rotate_z', 0)
        subtract = prim.get('subtract', False)

        glPushMatrix()
        glTranslatef(x, y, z)

        if rx:
            glRotatef(rx, 1, 0, 0)

        if ry:
            glRotatef(ry, 0, 1, 0)

        if rz:
            glRotatef(rz, 0, 0, 1)

        if selected:
            glColor3f(1.0, 0.85, 0.15)
            glDisable(GL_BLEND)

        elif subtract:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(1.0, 0.25, 0.25, 0.3)

        else:
            glDisable(GL_BLEND)
            glColor3f(*PALETTE[index % len(PALETTE)])

        q = gluNewQuadric()
        gluQuadricNormals(q, GLU_SMOOTH)

        self._dispatch_solid(ptype, w, d, h, r, r2, depth, q, prim)

        gluDeleteQuadric(q)

        self._draw_wireframe(ptype, w, d, h, r, selected)

        if selected:
            self._draw_bbox(ptype, w, d, h, r)

        glPopMatrix()

    def _dispatch_solid(self, ptype, w, d, h, r, r2, depth, q, prim):
        if ptype in _BOX_TYPES:
            _box(w, d, h)

        elif ptype == 'wedge':
            _wedge(w, d, h)

        elif ptype == 'prism':
            _prism(w, d, h)

        elif ptype == 'pyramid':
            _pyramid(w, d, h)

        elif ptype == 'cylinder':
            _cylinder(q, r, h)

        elif ptype == 'pipe':
            _pipe(q, r, h, depth)

        elif ptype == 'cone':
            _cone(q, r, r2, h)

        elif ptype == 'sphere':
            gluSphere(q, r, 32, 20)

        elif ptype == 'torus':
            _torus(r, r2)

        elif ptype == 'arch':
            _arch(w, d, depth)

        elif ptype == 'spring':
            _spring(r, prim.get('turns', 5), prim.get('pitch', 3), r2)

        elif ptype == 'thread':
            _thread(q, r, h, prim.get('pitch', 2))

        elif ptype == 'gear':
            _gear(r, prim.get('teeth', 12), h)

        elif ptype == 'linear_array':
            _linear_array(prim)

        elif ptype == 'polar_array':
            _polar_array(prim)

        else:
            _box(w, d, h)

    def _draw_wireframe(self, ptype, w, d, h, r, selected):
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glColor4f(1, 1, 1, 0.5 if selected else 0.10)
        glLineWidth(2.0 if selected else 0.7)

        if ptype == 'wedge':
            _wedge(w, d, h)

        elif ptype == 'prism':
            _prism(w, d, h)

        elif ptype == 'pyramid':
            _pyramid(w, d, h)

        elif ptype in _BOX_TYPES:
            _box(w, d, h)

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glLineWidth(1.0)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def _draw_bbox(self, ptype, w, d, h, r):
        if ptype in _RADIAL_TYPES:
            w = d = r * 2

        hx, hy = w / 2, d / 2

        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1, 1, 0.3, 0.6)
        glLineWidth(1.5)
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(1, 0xAAAA)

        glBegin(GL_LINE_LOOP)
        glVertex3f(-hx, -hy, 0)
        glVertex3f(hx, -hy, 0)
        glVertex3f(hx, hy, 0)
        glVertex3f(-hx, hy, 0)
        glEnd()

        glBegin(GL_LINE_LOOP)
        glVertex3f(-hx, -hy, h)
        glVertex3f(hx, -hy, h)
        glVertex3f(hx, hy, h)
        glVertex3f(-hx, hy, h)
        glEnd()

        glBegin(GL_LINES)

        for sx in (-hx, hx):
            for sy in (-hy, hy):
                glVertex3f(sx, sy, 0)
                glVertex3f(sx, sy, h)

        glEnd()

        glDisable(GL_LINE_STIPPLE)
        glDisable(GL_BLEND)
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)

    def _pick(self, mx, my):
        if not self.model or not self.model.primitives:
            return -1

        buf = glSelectBuffer(1024)
        glRenderMode(GL_SELECT)
        glInitNames()
        glPushName(0)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()

        vp = glGetIntegerv(GL_VIEWPORT)
        gluPickMatrix(mx, vp[3] - my, 8, 8, vp)
        gluPerspective(45.0, self.width() / max(self.height(), 1), 0.5, 80000.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        sz = self._scene_size()
        dist = sz * 2.5 / self.zoom
        cx, cy, cz = self._scene_center()

        gluLookAt(
            cx + dist * 0.6, cy - dist * 0.8, cz + dist * 0.7,
            cx, cy, cz,
            0, 0, 1
        )

        glTranslatef(self.pan_x, self.pan_y, 0)
        glTranslatef(cx, cy, cz)
        glRotatef(self.rot_x, 1, 0, 0)
        glRotatef(self.rot_z, 0, 0, 1)
        glTranslatef(-cx, -cy, -cz)

        for i, prim in enumerate(self.model.primitives):
            glLoadName(i)
            ptype = prim.get('type', 'box')

            glPushMatrix()
            glTranslatef(prim.get('x', 0), prim.get('y', 0), prim.get('z', 0))

            rx = prim.get('rotate_x', 0)
            ry = prim.get('rotate_y', 0)
            rz = prim.get('rotate_z', 0)

            if rx:
                glRotatef(rx, 1, 0, 0)

            if ry:
                glRotatef(ry, 0, 1, 0)

            if rz:
                glRotatef(rz, 0, 0, 1)

            w = prim.get('w', 10)
            d = prim.get('d', 10)
            h = prim.get('h', 10)
            r = prim.get('radius', 5)

            q = gluNewQuadric()

            if ptype in ('cylinder', 'pipe', 'cone', 'spring', 'thread', 'gear'):
                gluCylinder(q, r, r, h, 12, 1)

            elif ptype == 'sphere':
                gluSphere(q, r, 12, 8)

            else:
                _box(w, d, h)

            gluDeleteQuadric(q)
            glPopMatrix()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        hits = glRenderMode(GL_RENDER)
        best = -1
        best_z = float('inf')

        for hit in hits:
            if hit.names and hit.near / 0xFFFFFFFF < best_z:
                best_z = hit.near / 0xFFFFFFFF
                best = hit.names[-1]

        return best

    def mousePressEvent(self, event):
        self._last = event.pos()
        self._rmb = event.button() == Qt.MouseButton.RightButton
        self._drag = False

    def mouseMoveEvent(self, event):
        dx = event.pos().x() - self._last.x()
        dy = event.pos().y() - self._last.y()

        self._last = event.pos()
        self._drag = True

        if self._rmb:
            pan_scale = self._scene_size() * 0.003

            self.pan_x += dx * pan_scale
            self.pan_y -= dy * pan_scale

        else:
            self.rot_z += dx * 0.5
            self.rot_x = max(-89, min(89, self.rot_x + dy * 0.5))

        self.update()

    def mouseReleaseEvent(self, event):
        if not self._drag and event.button() == Qt.MouseButton.LeftButton:
            idx = self._pick(event.pos().x(), event.pos().y())

            if idx >= 0:
                self.selected = idx
                self.primitive_selected.emit(idx, self.model.primitives[idx])

            else:
                self.selected = -1

            self.update()

    def wheelEvent(self, event):
        factor = 1.1 if event.angleDelta().y() > 0 else 0.91

        self.zoom = max(0.05, min(30.0, self.zoom * factor))
        self.update()

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()

        for qt_key, view_name in NUMPAD_VIEWS:
            if key == qt_key and mods & Qt.KeyboardModifier.KeypadModifier:
                self.set_view(view_name)

                return

        if key == Qt.Key.Key_R:
            self.set_view('iso')

            return

        if self.selected < 0 or not self.model:
            return

        prim = dict(self.model.primitives[self.selected])
        shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
        changed = True

        if key == Qt.Key.Key_Left:
            prim['x'] = round(prim.get('x', 0) - MOVE_STEP, 2)

        elif key == Qt.Key.Key_Right:
            prim['x'] = round(prim.get('x', 0) + MOVE_STEP, 2)

        elif key == Qt.Key.Key_Up:
            axis = 'z' if shift else 'y'
            prim[axis] = round(prim.get(axis, 0) + MOVE_STEP, 2)

        elif key == Qt.Key.Key_Down:
            axis = 'z' if shift else 'y'
            prim[axis] = round(prim.get(axis, 0) - MOVE_STEP, 2)

        elif key == Qt.Key.Key_BracketLeft:
            for dim in ('w', 'd', 'h', 'radius'):
                if dim in prim:
                    prim[dim] = max(1.0, round(prim[dim] - RESIZE_STEP, 2))

        elif key == Qt.Key.Key_BracketRight:
            for dim in ('w', 'd', 'h', 'radius'):
                if dim in prim:
                    prim[dim] = round(prim[dim] + RESIZE_STEP, 2)

        else:
            changed = False

        if changed:
            self.model.primitives[self.selected] = prim
            self.primitive_changed.emit(self.selected, prim)
            self.update()


def _box(w, d, h):
    hx, hy = w / 2, d / 2

    glBegin(GL_QUADS)

    glNormal3f(0, 0, 1)
    glVertex3f(-hx, -hy, h)
    glVertex3f(hx, -hy, h)
    glVertex3f(hx, hy, h)
    glVertex3f(-hx, hy, h)

    glNormal3f(0, 0, -1)
    glVertex3f(-hx, -hy, 0)
    glVertex3f(-hx, hy, 0)
    glVertex3f(hx, hy, 0)
    glVertex3f(hx, -hy, 0)

    glNormal3f(0, -1, 0)
    glVertex3f(-hx, -hy, 0)
    glVertex3f(hx, -hy, 0)
    glVertex3f(hx, -hy, h)
    glVertex3f(-hx, -hy, h)

    glNormal3f(0, 1, 0)
    glVertex3f(-hx, hy, 0)
    glVertex3f(-hx, hy, h)
    glVertex3f(hx, hy, h)
    glVertex3f(hx, hy, 0)

    glNormal3f(-1, 0, 0)
    glVertex3f(-hx, -hy, 0)
    glVertex3f(-hx, -hy, h)
    glVertex3f(-hx, hy, h)
    glVertex3f(-hx, hy, 0)

    glNormal3f(1, 0, 0)
    glVertex3f(hx, -hy, 0)
    glVertex3f(hx, hy, 0)
    glVertex3f(hx, hy, h)
    glVertex3f(hx, -hy, h)

    glEnd()

def _cylinder(q, r, h):
    glTranslatef(0, 0, h / 2)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, r, r, h, 32, 1)
    gluDisk(q, 0, r, 32, 1)
    glTranslatef(0, 0, h)
    gluDisk(q, 0, r, 32, 1)

def _pipe(q, r, h, wall):
    _cylinder(q, r, h)
    inner_r = max(r - wall, 0.3)
    glTranslatef(0, 0, -h)
    gluCylinder(q, inner_r, inner_r, h, 32, 1)

def _cone(q, r_base, r_top, h):
    r_top = max(r_top, 0.01)
    glTranslatef(0, 0, h / 2)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, r_base, r_top, h, 32, 1)
    gluDisk(q, 0, r_base, 32, 1)
    glTranslatef(0, 0, h)
    gluDisk(q, 0, r_top, 32, 1)

def _torus(R, r, seg_ring=24, seg_tube=48):
    for i in range(seg_tube):
        a0 = 2 * math.pi * i       / seg_tube
        a1 = 2 * math.pi * (i + 1) / seg_tube

        glBegin(GL_QUAD_STRIP)

        for j in range(seg_ring + 1):
            b = 2 * math.pi * j / seg_ring
            cb, sb = math.cos(b), math.sin(b)

            for a in (a0, a1):
                ca, sa = math.cos(a), math.sin(a)
                glNormal3f(cb * ca, cb * sa, sb)
                glVertex3f((R + r * cb) * ca, (R + r * cb) * sa, r * sb)

        glEnd()

def _wedge(w, d, h):
    hx, hy = w / 2, d / 2

    glBegin(GL_TRIANGLES)

    glNormal3f(0, -1, 0)
    glVertex3f(-hx, -hy, h)
    glVertex3f(hx, -hy, 0)
    glVertex3f(-hx, -hy, 0)

    glNormal3f(0, 1, 0)
    glVertex3f(-hx, hy, h)
    glVertex3f(-hx, hy, 0)
    glVertex3f(hx, hy, 0)

    glEnd()

    glBegin(GL_QUADS)

    glNormal3f(0, -1, 0)
    glVertex3f(-hx, -hy, 0)
    glVertex3f(hx, -hy, 0)
    glVertex3f(hx, -hy, 0)
    glVertex3f(-hx, -hy, h)

    glNormal3f(0, 1, 0)
    glVertex3f(-hx, hy, 0)
    glVertex3f(-hx, hy, h)
    glVertex3f(hx, hy, 0)
    glVertex3f(hx, hy, 0)

    glNormal3f(0, 0, -1)
    glVertex3f(-hx, -hy, 0)
    glVertex3f(hx, -hy, 0)
    glVertex3f(hx, hy, 0)
    glVertex3f(-hx, hy, 0)

    glNormal3f(-1, 0, 0)
    glVertex3f(-hx, -hy, 0)
    glVertex3f(-hx, -hy, h)
    glVertex3f(-hx, hy, h)
    glVertex3f(-hx, hy, 0)

    glEnd()

def _prism(w, d, h):
    hx, hy = w / 2, d / 2

    glBegin(GL_TRIANGLES)

    glNormal3f(0, 0, 1)
    glVertex3f(-hx, -hy, 0)
    glVertex3f(hx, -hy, 0)
    glVertex3f(0, hy, 0)

    glNormal3f(0, 0, -1)
    glVertex3f(-hx, -hy, h)
    glVertex3f(0, hy, h)
    glVertex3f(hx, -hy, h)

    glEnd()

    glBegin(GL_QUADS)

    glNormal3f(0, -1, 0)
    glVertex3f(-hx, -hy, 0)
    glVertex3f(hx, -hy, 0)
    glVertex3f(hx, -hy, h)
    glVertex3f(-hx, -hy, h)

    glEnd()

def _pyramid(w, d, h):
    hx, hy = w / 2, d / 2
    apex = (0, 0, h)

    glBegin(GL_QUADS)
    glNormal3f(0, 0, -1)
    glVertex3f(-hx, -hy, 0)
    glVertex3f(hx, -hy, 0)
    glVertex3f(hx, hy, 0)
    glVertex3f(-hx, hy, 0)
    glEnd()

    base_edges = [
        ((-hx, -hy, 0), (hx, -hy, 0)),
        ((hx, -hy, 0), (hx, hy, 0)),
        ((hx, hy, 0), (-hx, hy, 0)),
        ((-hx, hy, 0), (-hx, -hy, 0))
    ]

    for a, b in base_edges:
        nx = (b[1] - a[1]) * (apex[2] - a[2]) - (b[2] - a[2]) * (apex[1] - a[1])
        ny = (b[2] - a[2]) * (apex[0] - a[0]) - (b[0] - a[0]) * (apex[2] - a[2])
        nz = (b[0] - a[0]) * (apex[1] - a[1]) - (b[1] - a[1]) * (apex[0] - a[0])

        glBegin(GL_TRIANGLES)
        glNormal3f(nx, ny, nz)
        glVertex3f(*a)
        glVertex3f(*b)
        glVertex3f(*apex)
        glEnd()

def _spring(R, turns, pitch, r_wire, steps=16):
    total = int(turns * steps)

    glDisable(GL_LIGHTING)
    glColor3f(0.7, 0.7, 0.7)
    glLineWidth(2.0)
    glBegin(GL_LINE_STRIP)

    for i in range(total + 1):
        t = i / steps
        a = 2 * math.pi * t
        glVertex3f(R * math.cos(a), R * math.sin(a), t * pitch)

    glEnd()
    glLineWidth(1.0)
    glEnable(GL_LIGHTING)

def _thread(q, r, h, pitch):
    segs = max(2, int(h / pitch))
    seg_h = h / segs

    for i in range(segs):
        glPushMatrix()
        glTranslatef(0, 0, i * seg_h)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(q, r, r * 0.9, seg_h, 16, 1)
        glPopMatrix()

def _gear(r, teeth, h):
    addendum = r * 0.1
    segments = teeth * 4

    def _profile_vertex(i, z):
        a = 2 * math.pi * i / segments
        ri = r + addendum if (i // 2) % 2 == 0 else r - addendum * 0.5
        glVertex3f(ri * math.cos(a), ri * math.sin(a), z)

    glBegin(GL_TRIANGLE_FAN)
    glNormal3f(0, 0, 1)
    glVertex3f(0, 0, h)

    for i in range(segments + 1):
        _profile_vertex(i, h)

    glEnd()

    glBegin(GL_TRIANGLE_FAN)
    glNormal3f(0, 0, -1)
    glVertex3f(0, 0, 0)

    for i in range(segments + 1):
        _profile_vertex(i, 0)

    glEnd()

    glBegin(GL_QUAD_STRIP)

    for i in range(segments + 1):
        a = 2 * math.pi * i / segments
        ri = r + addendum if (i // 2) % 2 == 0 else r - addendum * 0.5
        nx, ny = math.cos(a), math.sin(a)
        glNormal3f(nx, ny, 0)
        glVertex3f(ri * nx, ri * ny, 0)
        glVertex3f(ri * nx, ri * ny, h)

    glEnd()

def _arch(w, d, depth, steps=32):
    outer_r = w / 2
    inner_r = max(outer_r - depth, 0.5)

    glBegin(GL_QUAD_STRIP)

    for i in range(steps + 1):
        a = math.pi * i / steps
        ca, sa = math.cos(a), math.sin(a)
        glNormal3f(ca, 0, sa)
        glVertex3f(ca * outer_r, 0, sa * outer_r)
        glVertex3f(ca * inner_r, 0, sa * inner_r)

    glEnd()

    for y_pos in (0.0, float(d)):
        normal_y = -1.0 if y_pos == 0.0 else 1.0
        glBegin(GL_QUAD_STRIP)

        for i in range(steps + 1):
            a = math.pi * i / steps
            ca, sa = math.cos(a), math.sin(a)
            glNormal3f(0, normal_y, 0)
            glVertex3f(ca * outer_r, y_pos, sa * outer_r)
            glVertex3f(ca * inner_r, y_pos, sa * inner_r)

        glEnd()

def _linear_array(prim):
    w = prim.get('w', 10)
    d = prim.get('d', 10)
    h = prim.get('h', 10)
    count = prim.get('count', 3)
    count_y = prim.get('count_y', 1)
    dx = prim.get('dx', 20)
    dy = prim.get('dy', 0)

    for row in range(count_y):
        for col in range(count):
            glPushMatrix()
            glTranslatef(col * dx, row * dy, 0)
            _box(w, d, h)
            glPopMatrix()


def _polar_array(prim):
    radius = prim.get('radius', 5)
    h = prim.get('h', 10)
    count = max(1, prim.get('count', 6))
    total_a = prim.get('angle_total', 360)
    R = prim.get('w', 30)

    for i in range(count):
        a = math.radians(total_a * i / count)

        glPushMatrix()
        glTranslatef(R * math.cos(a), R * math.sin(a), 0)

        q = gluNewQuadric()
        gluQuadricNormals(q, GLU_SMOOTH)
        gluCylinder(q, radius, radius, h, 16, 1)
        gluDeleteQuadric(q)

        glPopMatrix()


class Viewer3DPanel(QWidget):
    primitive_selected = pyqtSignal(int, dict)
    primitive_changed = pyqtSignal(int, dict)

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())

        self.gl = GLViewer()
        self.gl.primitive_selected.connect(self.primitive_selected)
        self.gl.primitive_changed.connect(self.primitive_changed)
        root.addWidget(self.gl)

        root.addWidget(self._build_hint())

    def _build_toolbar(self):
        bar = QWidget()
        bar.setStyleSheet('background:#161616; border-bottom:1px solid #222;')

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(3)

        label = QLabel('View:')
        label.setStyleSheet('color:#555; font-size:11px;')
        layout.addWidget(label)

        for view_key, (_, _, view_label) in VIEWS.items():
            btn = QPushButton(view_label)
            btn.setFixedSize(46, 22)
            btn.setStyleSheet(
                'font-size:10px; padding:0; background:#222;'
                'border:1px solid #333; border-radius:3px; color:#aaa;'
            )
            btn.clicked.connect(lambda _, k=view_key: self.gl.set_view(k))
            layout.addWidget(btn)

        layout.addStretch()

        numpad_hint = QLabel('Num 1/3/7/9/0')
        numpad_hint.setStyleSheet('color:#333; font-size:10px;')
        layout.addWidget(numpad_hint)

        return bar

    def _build_hint(self):
        hint = QLabel(
            '  LMB rotate · RMB pan · Scroll zoom · R reset  '
            '│  Click = select  '
            '│  ←→↑↓ move · Shift+↑↓ = Z · [ ] resize'
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet('color:#333; font-size:10px; padding:3px; background:#0e0e0e;')

        return hint

    def load_model(self, model):
        self.gl.load_model(model)

    def select(self, index):
        self.gl.select(index)
