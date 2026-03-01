import sys
import io
import re
import math
import contextlib
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox, QTextEdit,
    QFileDialog, QProgressBar, QSplitter, QTabWidget, QScrollArea,
    QFrame, QSizePolicy, QToolTip, QMessageBox, QAction, QGraphicsOpacityEffect
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QRectF, QRect,
    QPropertyAnimation, QEasingCurve, QPoint
)
from PyQt5.QtGui import (
    QColor, QFont, QPainter, QBrush, QPen,
    QLinearGradient, QRadialGradient, QDragEnterEvent, QDropEvent,
    QTextCursor, QPainterPath, QFontMetrics
)

# ── ultrastack import ─────────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent))
    import ultrastack as us
    ULTRASTACK_AVAILABLE = True
    _IMPORT_ERROR = ""
except ImportError as _e:
    ULTRASTACK_AVAILABLE = False
    _IMPORT_ERROR = str(_e)


DEV_NAME    = "Ranasurya Ghosh"
DEV_EMAIL   = "ranasuryaghosh@gmail.com"
DEV_GITHUB  = "github.com/NuclearVenom"

# ══════════════════════════════════════════════════════════════════════════════
# PALETTE
# ══════════════════════════════════════════════════════════════════════════════
C = {
    "bg":          "#0d0f14",
    "surface":     "#13161e",
    "surface2":    "#1a1e2a",
    "surface3":    "#222736",
    "border":      "#2a2f3d",
    "border_hi":   "#3d4560",
    "accent":      "#4f7cff",
    "accent_glow": "#2d4cb8",
    "accent2":     "#7c4fff",
    "success":     "#3ecf8e",
    "warning":     "#f5a623",
    "danger":      "#e05252",
    "text":        "#dde2f0",
    "text_dim":    "#6b748f",
    "text_bright": "#ffffff",
}

STYLESHEET = f"""
QWidget {{
    background-color: {C['bg']};
    color: {C['text']};
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
}}
QMainWindow {{ background-color: {C['bg']}; }}
QSplitter::handle {{ background: {C['border']}; width: 2px; height: 2px; }}

QGroupBox {{
    background-color: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 10px;
    margin-top: 16px;
    padding: 14px 12px 12px 12px;
    font-size: 12px; font-weight: 600;
    color: {C['text_dim']}; letter-spacing: 0.8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    padding: 2px 10px; color: {C['text_dim']}; background: transparent;
}}
QTabWidget::pane {{
    border: 1px solid {C['border']}; border-radius: 8px;
    background: {C['surface']}; margin-top: -1px;
}}
QTabBar::tab {{
    background: {C['surface2']}; color: {C['text_dim']};
    border: 1px solid {C['border']}; border-bottom: none;
    border-radius: 6px 6px 0 0; padding: 8px 16px;
    margin-right: 2px; font-size: 13px; font-weight: 500;
}}
QTabBar::tab:selected {{ background: {C['surface']}; color: {C['text']}; border-color: {C['border_hi']}; }}
QTabBar::tab:hover:!selected {{ background: {C['surface3']}; color: {C['text']}; }}
QPushButton {{
    background-color: {C['surface3']}; color: {C['text']};
    border: 1px solid {C['border']}; border-radius: 7px;
    padding: 8px 16px; font-size: 13px; font-weight: 500;
}}
QPushButton:hover {{ background-color: {C['border_hi']}; border-color: {C['accent']}; color: {C['text_bright']}; }}
QPushButton:pressed {{ background-color: {C['accent_glow']}; }}
QPushButton:disabled {{ background-color: {C['surface']}; color: {C['text_dim']}; border-color: {C['border']}; }}
QPushButton#danger {{ background: {C['surface3']}; color: {C['danger']}; border: 1px solid {C['danger']}; }}
QPushButton#danger:hover {{ background: {C['danger']}; color: white; }}
QLineEdit, QTextEdit {{
    background-color: {C['surface2']}; color: {C['text']};
    border: 1px solid {C['border']}; border-radius: 7px;
    padding: 7px 10px; selection-background-color: {C['accent']};
}}
QLineEdit:focus, QTextEdit:focus {{ border-color: {C['accent']}; }}
QLineEdit:hover {{ border-color: {C['border_hi']}; }}
QComboBox {{
    background-color: {C['surface2']}; color: {C['text']};
    border: 1px solid {C['border']}; border-radius: 7px; padding: 7px 10px;
}}
QComboBox:hover {{ border-color: {C['border_hi']}; }}
QComboBox:focus {{ border-color: {C['accent']}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 6px solid {C['text_dim']}; margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {C['surface2']}; color: {C['text']};
    border: 1px solid {C['border_hi']}; border-radius: 6px;
    selection-background-color: {C['accent']}; outline: none;
}}
QSpinBox, QDoubleSpinBox {{
    background-color: {C['surface2']}; color: {C['text']};
    border: 1px solid {C['border']}; border-radius: 7px; padding: 6px 8px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {C['accent']}; }}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background: {C['surface3']}; border: none; border-radius: 3px; width: 18px;
}}
QCheckBox {{ color: {C['text']}; spacing: 10px; font-size: 14px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border: 2px solid {C['border_hi']};
    border-radius: 5px; background: {C['surface2']};
}}
QCheckBox::indicator:checked {{ background: {C['accent']}; border-color: {C['accent']}; }}
QCheckBox::indicator:hover {{ border-color: {C['accent']}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: {C['surface']}; width: 7px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {C['border_hi']}; border-radius: 3px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: {C['surface']}; height: 7px; }}
QScrollBar::handle:horizontal {{ background: {C['border_hi']}; border-radius: 3px; }}
QProgressBar {{
    background-color: {C['surface2']}; border: 1px solid {C['border']};
    border-radius: 6px; height: 10px; text-align: center;
    font-size: 11px; color: {C['text_dim']};
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {C['accent']},stop:1 {C['accent2']});
    border-radius: 5px;
}}
QStatusBar {{
    background: {C['surface']}; color: {C['text_dim']};
    border-top: 1px solid {C['border']}; font-size: 12px; padding: 2px 8px;
}}
QToolTip {{
    background-color: {C['surface3']}; color: {C['text']};
    border: 1px solid {C['accent']}; border-radius: 6px;
    padding: 7px 11px; font-size: 12px;
}}
QLabel {{ background: transparent; color: {C['text']}; }}
QLabel#title  {{ font-size: 25px; font-weight: 700; color: {C['text_bright']}; letter-spacing: 2px; }}
QLabel#subtitle {{ font-size: 13px; color: #a0aac8; letter-spacing: 0.4px; }}
QLabel#sectionhead {{ font-size: 11px; font-weight: 700; color: {C['text_dim']}; letter-spacing: 1.2px; }}
QTextEdit#console {{
    background: #080a0f; color: #a0c4ff;
    border: 1px solid {C['border']}; border-radius: 8px;
    font-family: 'Cascadia Code','Fira Code','JetBrains Mono','Consolas',monospace;
    font-size: 12px; padding: 10px;
}}
QTextEdit#syslog {{
    background: #070810; color: {C['text_dim']};
    border: 1px solid {C['border']}; border-radius: 6px;
    font-family: 'Cascadia Code','Fira Code','Consolas',monospace;
    font-size: 12px; padding: 8px;
}}
QLabel#dropzone {{
    background-color: {C['surface2']}; border: 2px dashed {C['border_hi']};
    border-radius: 10px; color: {C['text_dim']}; font-size: 13px; padding: 18px;
}}
QLabel#dropzone:hover {{
    border-color: {C['accent']}; color: {C['text']}; background-color: {C['surface3']};
}}
QFrame[frameShape="4"], QFrame[frameShape="5"] {{ color: {C['border']}; }}
QMenuBar {{ background: {C['surface']}; border-bottom: 1px solid {C['border']}; }}
QMenuBar::item {{ padding: 6px 12px; color: {C['text_dim']}; }}
QMenuBar::item:selected {{ background: {C['surface3']}; color: {C['text']}; }}
QMenu {{
    background: {C['surface2']}; border: 1px solid {C['border_hi']};
    border-radius: 8px; padding: 4px;
}}
QMenu::item {{ padding: 8px 20px; border-radius: 5px; color: {C['text']}; }}
QMenu::item:selected {{ background: {C['accent']}; color: white; }}
"""


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def tip(w, text: str):
    w.setToolTip(text); w.setToolTipDuration(9000)

def labeled_row(label_text: str, widget, tip_text: str = "",
                label_width: int = 145) -> QHBoxLayout:
    row = QHBoxLayout()
    lbl = QLabel(label_text)
    lbl.setFixedWidth(label_width)
    lbl.setStyleSheet(f"color:{C['text_dim']}; font-size:13px;")
    row.addWidget(lbl); row.addWidget(widget, 1)
    if tip_text: tip(widget, tip_text); tip(lbl, tip_text)
    return row

def section_label(text: str) -> QLabel:
    lbl = QLabel(text); lbl.setObjectName("sectionhead"); return lbl

def h_line() -> QFrame:
    f = QFrame(); f.setFrameShape(QFrame.HLine); f.setFrameShadow(QFrame.Sunken); return f


# ══════════════════════════════════════════════════════════════════════════════
# SPLASH SCREEN
# ══════════════════════════════════════════════════════════════════════════════

class SplashScreen(QWidget): 
    done = pyqtSignal()

    W, H        = 550, 300
    MARGIN      = 0
    TITLE_Y     = 138
    STATUS_TOP  = 180
    LINE_H      = 26
    MAX_LINES   = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.W, self.H)

        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center().x() - self.W // 2,
                  screen.center().y() - self.H // 2)

        import random
        rng = random.Random(7)
        # (x, y, drift_speed, base_brightness, twinkle_range, phase)
        self._stars = [
            (rng.uniform(0, self.W),
             rng.uniform(0, self.H),
             rng.uniform(0.10, 0.45),
             rng.randint(50, 120),
             rng.randint(0, 35),
             rng.uniform(0, 6.28))
            for _ in range(120)
        ]
        self._tick_n   = 0
        self._pulse    = 0.0
        self._pulse_d  = 1
        self._lines    = []          # list of (full_text, chars_shown)
        self._type_idx = -1          # index of line being typed
        self._type_pos = 0
        self._cur_vis  = True        # cursor blink state
        self._fade     = 1.0

        self._frame_t = QTimer(self)
        self._frame_t.timeout.connect(self._frame_tick)
        self._frame_t.start(22)

        self._type_t = QTimer(self)
        self._type_t.timeout.connect(self._type_tick)
        self._type_t.start(28)

        self._cur_t = QTimer(self)
        self._cur_t.timeout.connect(self._cur_tick)
        self._cur_t.start(520)

        self._fade_t = QTimer(self)
        self._fade_t.timeout.connect(self._fade_tick)

    # ── ticks ─────────────────────────────────────────────────────────────────
    def _frame_tick(self):
        self._tick_n += 1
        drifted = []
        for x, y, spd, bb, br, ph in self._stars:
            y = (y + spd) % (self.H + 4)
            drifted.append((x, y, spd, bb, br, ph))
        self._stars = drifted
        self._pulse += 0.022 * self._pulse_d
        if self._pulse >= 1.0: self._pulse_d = -1
        if self._pulse <= 0.0: self._pulse_d =  1
        self.update()

    def _type_tick(self):
        if 0 <= self._type_idx < len(self._lines):
            full, shown = self._lines[self._type_idx]
            if shown < len(full):
                self._lines[self._type_idx] = (full, shown + 1)
                self.update()

    def _cur_tick(self):
        self._cur_vis = not self._cur_vis
        self.update()

    def _fade_tick(self):
        self._fade -= 0.055
        if self._fade <= 0.0:
            self._fade = 0.0
            self._fade_t.stop()
            self._frame_t.stop()
            self._type_t.stop()
            self._cur_t.stop()
            self.done.emit()
            self.hide()
        self.update()

    # ── public ────────────────────────────────────────────────────────────────
    def set_status(self, text: str):
        self._lines.append((text, 0))
        if len(self._lines) > self.MAX_LINES:
            self._lines = self._lines[-self.MAX_LINES:]
        self._type_idx = len(self._lines) - 1
        self._type_pos = 0
        self.update()

    def fade_out(self):
        self._fade_t.start(18)

    # ── paint ─────────────────────────────────────────────────────────────────
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setOpacity(self._fade)
        w, h = self.W, self.H

        # Rounded clipping path
        radius = 10
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
        p.setClipPath(path)

        # Pure black background
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#000000")))
        p.drawRoundedRect(QRectF(0, 0, w, h), radius, radius)

        # Drifting micro-stars
        for x, y, spd, bb, br, ph in self._stars:
            twinkle = int(br * math.sin(ph + self._tick_n * 0.05))
            bright  = max(28, min(185, bb + twinkle))
            r       = 0.65 if spd < 0.22 else 0.4
            col     = QColor(bright, bright, bright + 12)
            p.setPen(col)
            p.setBrush(QBrush(col))
            p.drawEllipse(QRectF(x - r, y - r, r * 2, r * 2))

        # Soft glow halo behind title
        glow_a = int(16 + 10 * self._pulse)
        glow   = QRadialGradient(w / 2, self.TITLE_Y, 140)
        glow.setColorAt(0.0, QColor(55, 95, 255, glow_a))
        glow.setColorAt(1.0, QColor(55, 95, 255, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QRectF(w / 2 - 140, self.TITLE_Y - 42, 280, 84))

        # ULTRASTACK title
        tf = QFont("Segoe UI", 28, QFont.Bold)
        tf.setLetterSpacing(QFont.AbsoluteSpacing, 5)
        p.setFont(tf)
        # soft glow layer
        p.setPen(QColor(90, 140, 255, 45))
        p.drawText(QRect(2, self.TITLE_Y - 22, w, 44),
                   Qt.AlignHCenter | Qt.AlignVCenter, "ULTRASTACK")
        # crisp white layer
        p.setPen(QColor(230, 236, 255))
        p.drawText(QRect(0, self.TITLE_Y - 22, w, 44),
                   Qt.AlignHCenter | Qt.AlignVCenter, "ULTRASTACK")

        # Thin gradient underline
        ul_w = 110
        ul_x = (w - ul_w) // 2
        ul_y = self.TITLE_Y + 25
        ul_g = QLinearGradient(ul_x, 0, ul_x + ul_w, 0)
        ul_g.setColorAt(0.0, QColor(79, 124, 255, 0))
        ul_g.setColorAt(0.5, QColor(79, 124, 255, 160))
        ul_g.setColorAt(1.0, QColor(79, 124, 255, 0))
        p.setPen(QPen(QBrush(ul_g), 1))
        p.drawLine(ul_x, ul_y, ul_x + ul_w, ul_y)

        # Status lines — typewritten, left-aligned
        sf = QFont("Segoe UI", 11)
        p.setFont(sf)
        for i, (full_text, shown) in enumerate(self._lines):
            yp        = self.STATUS_TOP + i * self.LINE_H
            is_active = (i == len(self._lines) - 1)
            age       = len(self._lines) - 1 - i

            if is_active:
                text_col = QColor(C["accent"])
            else:
                a = max(55, 175 - age * 38)
                text_col = QColor(110, 135, 175, a)

            # bullet
            p.setPen(QColor(C["border_hi"]))
            p.drawText(QRect(self.MARGIN, yp, 16, self.LINE_H),
                       Qt.AlignLeft | Qt.AlignVCenter, "›")

            # revealed text
            visible = full_text[:shown]
            p.setPen(text_col)
            p.drawText(QRect(self.MARGIN + 18, yp, w - self.MARGIN - 28, self.LINE_H),
                       Qt.AlignLeft | Qt.AlignVCenter, visible)

            # blinking cursor on active line while still typing
            if is_active and shown < len(full_text) and self._cur_vis:
                fm   = p.fontMetrics()
                tx_w = fm.horizontalAdvance(visible)
                p.setPen(QColor(C["accent"]))
                p.drawText(QRect(self.MARGIN + 18 + tx_w + 2, yp, 14, self.LINE_H),
                           Qt.AlignLeft | Qt.AlignVCenter, "▌")

        # Developer credit — bottom-left, clearly visible
        cf = QFont("Segoe UI", 10)
        p.setFont(cf)
        p.setPen(QColor(165, 175, 200, 210))
        p.drawText(QRect(self.MARGIN, h - 30, w, 28),
                   Qt.AlignRight, f"Created by {DEV_NAME} ")

# ══════════════════════════════════════════════════════════════════════════════
# ANIMATED GRADIENT HEADER
# ══════════════════════════════════════════════════════════════════════════════

class GradientHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self._t = 0.0
        t = QTimer(self); t.timeout.connect(self._tick); t.start(40)

    def _tick(self):
        self._t = (self._t + 0.003) % 1.0; self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), 0)
        o = self._t
        g.setColorAt((o + 0.00) % 1.0, QColor("#0d0f14"))
        g.setColorAt((o + 0.25) % 1.0, QColor("#141840"))
        g.setColorAt((o + 0.50) % 1.0, QColor("#1e3080"))
        g.setColorAt((o + 0.75) % 1.0, QColor("#141840"))
        g.setColorAt(1.0,               QColor("#0d0f14"))
        p.fillRect(self.rect(), QBrush(g))
        pen = QPen(QColor("#4f7cff44")); pen.setWidth(1); p.setPen(pen)
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)


# ══════════════════════════════════════════════════════════════════════════════
# WAVE SHIMMER RUN BUTTON
# ══════════════════════════════════════════════════════════════════════════════

class WaveRunButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(220, 48)
        self._wave = 0.0
        self._hover = False
        self._down  = False
        t = QTimer(self); t.timeout.connect(self._tick); t.start(20)

    def _tick(self):
        self._wave = (self._wave + 0.005) % 1.0; self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, w, h), 10, 10)
        p.setClipPath(clip)
        if self._down:
            c1, c2 = QColor("#253880"), QColor("#4a2a90")
        elif self._hover:
            c1, c2 = QColor("#6090ff"), QColor("#9a60ff")
        else:
            c1, c2 = QColor("#4f7cff"), QColor("#7c4fff")
        bg = QLinearGradient(0, 0, w, 0)
        bg.setColorAt(0.0, c1); bg.setColorAt(1.0, c2)
        p.fillPath(clip, QBrush(bg))
        cx = self._wave * (w + 140) - 70
        alpha = 60 if not self._hover else 90
        sh = QLinearGradient(cx - 70, 0, cx + 70, 0)
        sh.setColorAt(0.00, QColor(255, 255, 255, 0))
        sh.setColorAt(0.40, QColor(255, 255, 255, 0))
        sh.setColorAt(0.50, QColor(255, 255, 255, alpha))
        sh.setColorAt(0.60, QColor(255, 255, 255, 0))
        sh.setColorAt(1.00, QColor(255, 255, 255, 0))
        p.fillPath(clip, QBrush(sh))
        p.setClipping(False)
        p.setPen(QColor("#ffffff") if self.isEnabled() else QColor("#66666666"))
        f = self.font(); f.setBold(True); f.setPointSize(11); p.setFont(f)
        p.drawText(QRect(0, 0, w, h), Qt.AlignCenter, self.text())

    def enterEvent(self, e): self._hover = True;  self.update(); super().enterEvent(e)
    def leaveEvent(self, e): self._hover = False; self.update(); super().leaveEvent(e)
    def mousePressEvent(self, e):   self._down = True;  self.update(); super().mousePressEvent(e)
    def mouseReleaseEvent(self, e): self._down = False; self.update(); super().mouseReleaseEvent(e)


# ══════════════════════════════════════════════════════════════════════════════
# DRAG-AND-DROP ZONE
# ══════════════════════════════════════════════════════════════════════════════

class DropZone(QLabel):
    dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropzone"); self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True); self.setMinimumHeight(80); self._idle()

    def _idle(self):
        self.setText("⬇   Drag & drop a folder, video, or .ser file here\n"
                     "      — or use the Browse buttons below —")

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.setStyleSheet(
                f"background:{C['surface3']}; border:2px dashed {C['accent']};"
                f"border-radius:10px; color:{C['text']}; font-size:13px; padding:18px;")
            self.setText("  ✓  Release to load")

    def dragLeaveEvent(self, _): self.setStyleSheet(""); self._idle()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls: self.dropped.emit(urls[0].toLocalFile())
        self.setStyleSheet(""); self._idle()


# ══════════════════════════════════════════════════════════════════════════════
# WORKER THREAD
# ══════════════════════════════════════════════════════════════════════════════

class WorkerThread(QThread):
    log_line = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, cfg: dict):
        super().__init__(); self.cfg = cfg

    def run(self):
        if not ULTRASTACK_AVAILABLE:
            self.finished.emit(False, f"Cannot import ultrastack:\n{_IMPORT_ERROR}"); return

        cfg = self.cfg

        class Tee(io.StringIO):
            def __init__(self, sig): super().__init__(); self._s = sig
            def write(self, s):
                if s.strip(): self._s.emit(s.rstrip())
                return len(s)
            def flush(self): pass

        tee = Tee(self.log_line)
        self.log_line.emit("═" * 58)
        self.log_line.emit(f"  UltraStack  —  {datetime.now().strftime('%H:%M:%S')}")
        if cfg.get("lite"): self.log_line.emit("  ⚡  QUICK STACK mode active")
        self.log_line.emit("═" * 58)

        try:
            master_dark = None
            if cfg.get("dark"):
                with contextlib.redirect_stdout(tee):
                    master_dark = us.make_master_dark(cfg["dark"])

            device     = cfg["_device"]; torch_mod = cfg["_torch"]
            input_path = Path(cfg["input"]); ext = input_path.suffix.lower()
            self.log_line.emit(f"  Input  : {input_path}")
            self.log_line.emit(f"  Output : {cfg['output']}")

            if cfg.get("lite"):
                with contextlib.redirect_stdout(tee):
                    self._run_lite(cfg, input_path, ext, master_dark)
            else:
                common = dict(
                    output_path      = cfg["output"],
                    stack_mode       = cfg["mode"],
                    align_method     = cfg["align"],
                    enhance          = cfg["enhance"],
                    stretch          = cfg["stretch"],
                    master_dark      = master_dark,
                    hot_pixel_thresh = cfg["hot_pixels"],
                    device           = device,
                    torch_module     = torch_mod,
                )
                with contextlib.redirect_stdout(tee):
                    if input_path.is_dir():
                        us.run_folder_pipeline(
                            folder_path=str(input_path), stitch=cfg["stitch"],
                            stack_threshold=cfg["threshold"],
                            sigma_low=cfg["sigma_low"], sigma_high=cfg["sigma_high"],
                            sigma_iters=cfg["sigma_iters"], **common)
                    elif ext == ".ser":
                        us.run_ser_pipeline(
                            ser_path=str(input_path), frame_skip=cfg["skip"],
                            max_frames=cfg["max_frames"] or None,
                            sigma_low=cfg["sigma_low"], sigma_high=cfg["sigma_high"],
                            sigma_iters=cfg["sigma_iters"], **common)
                    elif ext in us.VIDEO_EXTENSIONS:
                        us.run_video_pipeline(
                            video_path=str(input_path), frame_skip=cfg["skip"],
                            max_frames=cfg["max_frames"] or None, **common)
                    else:
                        raise ValueError(f"Unsupported input: {input_path}")

            self.finished.emit(True, cfg["output"])

        except Exception as exc:
            import traceback
            self.log_line.emit(f"\n  ✗  ERROR: {exc}")
            self.log_line.emit(traceback.format_exc())
            self.finished.emit(False, str(exc))

    def _run_lite(self, cfg, input_path, ext, master_dark):
        import numpy as np, cv2
        skip_align = cfg.get("lite_skip_align", False)
        out_path   = cfg["output"]
        self.log_line.emit(
            f"  Align: {'none' if skip_align else 'ORB'}  |  Mode: average  |  Enhance: off")
        if input_path.is_dir():
            _, paths = us.detect_folder_format(str(input_path))
            self.log_line.emit(f"  Found {len(paths)} images")
            images = us.load_images_parallel(paths)
        elif ext == ".ser":
            ser = us.SERFile(str(input_path)); images = []
            for i, (_, frm) in enumerate(ser.frames(cfg.get("skip", 1),
                                                      cfg.get("max_frames") or None)):
                images.append(frm)
                if (i+1) % 100 == 0: self.log_line.emit(f"  Read {i+1} SER frames…")
            ser.close()
        elif ext in us.VIDEO_EXTENSIONS:
            cap = cv2.VideoCapture(str(input_path)); images = []
            skip = cfg.get("skip", 1); maxf = cfg.get("max_frames") or None; fi = 0
            while True:
                ret, frm = cap.read()
                if not ret: break
                if fi % skip == 0:
                    images.append(frm)
                    if len(images) % 100 == 0: self.log_line.emit(f"  Read {len(images)} frames…")
                fi += 1
                if maxf and len(images) >= maxf: break
            cap.release()
        else:
            raise ValueError(f"Unsupported: {input_path}")
        if not images: raise ValueError("No frames loaded")
        if master_dark is not None:
            self.log_line.emit("  Subtracting dark…")
            images = [us.subtract_dark(im, master_dark) for im in images]
        if not skip_align and len(images) > 1:
            self.log_line.emit(f"  Aligning {len(images)} frames…")
            base_gray = cv2.cvtColor(images[0], cv2.COLOR_BGR2GRAY)
            aligned = [images[0]]
            for i, img in enumerate(images[1:], 1):
                aligned.append(us.align_frame(base_gray, img, "orb"))
                if i % 50 == 0: self.log_line.emit(f"  Aligned {i}/{len(images)-1}…")
            images = aligned
        self.log_line.emit(f"  Stacking {len(images)} frames…")
        acc = images[0].astype("float64")
        for k, img in enumerate(images[1:], 1):
            acc += (img.astype("float64") - acc) / (k + 1)
            if k % 100 == 0: self.log_line.emit(f"  Stacked {k+1}/{len(images)}…")
        result = np.clip(acc, 0, 255).astype("uint8")
        lite_fmt = cfg.get("lite_fmt", "jpg")
        p = Path(out_path)
        if p.suffix.lower().lstrip(".") != lite_fmt:
            out_path = str(p.parent / f"{p.stem}_quick.{lite_fmt}")
            cfg["output"] = out_path
        us.save_output(result, out_path)
        us.print_image_stats(result, out_path)


# ══════════════════════════════════════════════════════════════════════════════
# GPU PROBE
# ══════════════════════════════════════════════════════════════════════════════

class GPUProbeThread(QThread):
    result = pyqtSignal(str, str, object, object)
    status = pyqtSignal(str)   # incremental status for splash

    def run(self):
        self.status.emit("Probing GPU…  Please wait")
        try:
            self.status.emit("Loading PyTorch…")
            device, torch_mod = (
                us.setup_device(force_cpu=False)
                if ULTRASTACK_AVAILABLE else ("cpu", None)
            )
            if device == "cuda":
                import torch
                self.status.emit("Reading GPU properties…")
                name = torch.cuda.get_device_name(0)
                vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
                self.result.emit(f"✓  {name}  ({vram:.1f} GB)", "ok", device, torch_mod)
            else:
                self.result.emit("⚠  No CUDA GPU — CPU mode", "warn", device, torch_mod)
        except Exception as e:
            self.result.emit(f"✗  {e}", "err", "cpu", None)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ══════════════════════════════════════════════════════════════════════════════

class UltraStackGUI(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("UltraStack v2  —  Astronomical Image Stacking")
        self.setMinimumSize(1100, 720)
        self.resize(1320, 860)

        self._device = "cpu"
        self._torch  = None
        self._worker = None

        self._build_ui()

        # ── Splash screen + GPU probe ─────────────────────────────────────────
        self._splash = SplashScreen()
        self._splash.show()
        self.hide()   # keep main window hidden until splash finishes

        self._probe = GPUProbeThread()
        self._probe.status.connect(self._splash.set_status)
        self._probe.result.connect(self._on_gpu_result)
        self._probe.start()

    # ── GPU result arrives ────────────────────────────────────────────────────
    def _on_gpu_result(self, text, kind, device, torch_mod):
        self._device = device
        self._torch  = torch_mod

        cols = {"ok": C["success"], "warn": C["warning"], "err": C["danger"]}
        col  = cols.get(kind, C["text_dim"])

        # Update badge — GPU status only (no error text dumped into header)
        self._gpu_badge.setStyleSheet(
            f"color:{col}; font-size:12px; font-weight:600; background:transparent;")
        badge_icons = {"ok": "●  GPU", "warn": "●  CPU", "err": "●  CPU"}
        self._gpu_badge.setText(badge_icons.get(kind, "●"))

        if kind == "ok":
            import torch
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            self._gpu_detail.setText(f"{name}  ·  {vram:.1f} GB VRAM")
            self._gpu_detail.setStyleSheet(f"color:{C['success']}; font-size:11px; background:transparent;")
        elif kind == "warn":
            self._gpu_detail.setText("No CUDA GPU — running on CPU")
            self._gpu_detail.setStyleSheet(f"color:{C['warning']}; font-size:11px; background:transparent;")
        else:
            # Error: show brief note in detail line only — NOT in the banner
            self._gpu_detail.setText("GPU unavailable — CPU mode active")
            self._gpu_detail.setStyleSheet(f"color:{C['text_dim']}; font-size:11px; background:transparent;")

        # Route full error message to system log only
        icon = {"ok": "✓", "warn": "⚠", "err": "✗"}.get(kind, "•")
        self._sys_append(f"{icon}  {text}", col)
        if kind == "err":
            self._sys_append(
                "    Likely cause: PyTorch CUDA build does not match your\n"
                "    installed CUDA version  (e.g. torch+cu121 on CUDA 12.4).\n"
                "    Fix: pytorch.org → Get Started → correct CUDA build.\n"
                "    UltraStack runs fully on CPU — no action required.",
                C["text_dim"])
            self._syslog_panel.setVisible(True)
        elif kind == "warn":
            self._syslog_panel.setVisible(True)

        self.statusBar().showMessage(f"  {text}")

        # Fade splash, show main window
        self._splash.set_status("Ready!" if kind == "ok" else
                                 "CPU mode — ready!" if kind == "warn" else
                                 "GPU unavailable — CPU mode ready")
        QTimer.singleShot(600, self._finish_splash)

    def _finish_splash(self):
        self._splash.done.connect(self._show_main)
        self._splash.fade_out()

    def _show_main(self):
        self.show()
        self.raise_()

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        self._build_menu()
        root.addWidget(self._build_header())
        sp = QSplitter(Qt.Horizontal)
        sp.setHandleWidth(3); sp.setChildrenCollapsible(False)
        sp.addWidget(self._build_left()); sp.addWidget(self._build_right())
        sp.setSizes([700, 440])
        root.addWidget(sp, 1)
        root.addWidget(self._build_bottom_bar())

    # ── Menu ──────────────────────────────────────────────────────────────────
    def _build_menu(self):
        mb = self.menuBar()
        fm = mb.addMenu("File")
        a = QAction("Open Input…", self); a.triggered.connect(self._browse_input); fm.addAction(a)
        a2 = QAction("Quit", self);       a2.triggered.connect(self.close);        fm.addAction(a2)
        hm = mb.addMenu("Help")
        a3 = QAction("About UltraStack", self); a3.triggered.connect(self._show_about); hm.addAction(a3)

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self) -> QWidget:
        hdr = GradientHeader()
        lay = QHBoxLayout(hdr); lay.setContentsMargins(28, 0, 20, 0)

        # Left: title + subtitle
        title = QLabel("ULTRASTACK"); title.setObjectName("title"); title.setStyleSheet("font-size:38px")
        sub   = QLabel("Both GPU & CPU Compatible Image Stacking for Astronomical or Casual use"); sub.setObjectName("subtitle"); sub.setStyleSheet("font-size:14px")
        lv = QVBoxLayout(); lv.setSpacing(3)
        lv.addWidget(title); lv.addWidget(sub)

        # Centre: GPU status badge (just a coloured dot + label — no error text)
        self._gpu_badge  = QLabel("●  Probing…")
        self._gpu_badge.setStyleSheet(
            f"color:{C['warning']}; font-size:12px; font-weight:600; background:transparent;")
        self._gpu_badge.setAlignment(Qt.AlignCenter)
        self._gpu_detail = QLabel("")
        self._gpu_detail.setStyleSheet(
            f"color:{C['text_dim']}; font-size:11px; background:transparent;")
        self._gpu_detail.setAlignment(Qt.AlignCenter)
        gpu_col = QVBoxLayout(); gpu_col.setSpacing(1)
        gpu_col.addWidget(self._gpu_badge); gpu_col.addWidget(self._gpu_detail)

        # Right: developer info
        dev = QLabel("Developed by,")
        dev.setStyleSheet(
            f"color:{C['text_dim']}; font-size:12px; background:transparent;")
        dev.setAlignment(Qt.AlignRight)

        dev_name_lbl = QLabel(DEV_NAME)
        dev_name_lbl.setStyleSheet(
            f"color:{C['text_dim']}; font-size:16px; font-weight:600; background:transparent;")
        dev_name_lbl.setAlignment(Qt.AlignRight)

        dev_email_lbl = QLabel(DEV_EMAIL)
        dev_email_lbl.setStyleSheet(
            f"color:{C['text_dim']}; font-size:14px; background:transparent;")
        dev_email_lbl.setAlignment(Qt.AlignRight)

        dev_github_lbl = QLabel(DEV_GITHUB)
        dev_github_lbl.setStyleSheet(
            f"color:{C['accent']}; font-size:14px; background:transparent;")
        dev_github_lbl.setAlignment(Qt.AlignRight)

        dev_col = QVBoxLayout(); dev_col.setSpacing(1)
        dev_col.addWidget(dev)
        dev_col.addWidget(dev_name_lbl)
        dev_col.addWidget(dev_email_lbl)
        dev_col.addWidget(dev_github_lbl)

        lay.addLayout(lv)
        lay.addStretch()
        lay.addLayout(gpu_col)
        lay.addSpacing(30)
        lay.addLayout(dev_col)
        return hdr

    # ── Left ──────────────────────────────────────────────────────────────────
    def _build_left(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        w = QWidget(); lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 14, 10, 14); lay.setSpacing(12)
        lay.addWidget(self._build_io_group())
        lay.addWidget(self._build_tabs())
        lay.addStretch()
        scroll.setWidget(w); return scroll

    # ── I/O group ─────────────────────────────────────────────────────────────
    def _build_io_group(self) -> QGroupBox:
        box = QGroupBox("Input / Output"); lay = QVBoxLayout(box); lay.setSpacing(9)
        self._drop = DropZone(); self._drop.dropped.connect(self._on_drop); lay.addWidget(self._drop)

        self._inp = QLineEdit()
        self._inp.setPlaceholderText("Paste path to folder, video (.mp4, .avi…), or .ser file…")
        tip(self._inp,
            "Enter the full path to:\n"
            "• A folder of images (JPG / PNG / TIFF / FITS / BMP / WEBP)\n"
            "• A video file (MP4, AVI, MOV, MKV, TS, …)\n"
            "• A SER file (astronomical capture — FireCapture, SharpCap)\n\n"
            "Tip: drag & drop the folder or file into the zone above.")
        self._inp.textChanged.connect(self._on_input_changed)
        bi = QPushButton("📁  Browse"); tip(bi, "Open a file/folder picker"); bi.clicked.connect(self._browse_input)
        ri = QHBoxLayout(); ri.addWidget(QLabel("Input:")); ri.addWidget(self._inp, 1); ri.addWidget(bi); lay.addLayout(ri)

        self._out = QLineEdit()
        self._out.setPlaceholderText("Output filename  (e.g.  stacked.tif  or  result.jpg)")
        tip(self._out,
            "Output file path. Extension controls format:\n"
            "  .jpg / .jpeg  →  JPEG quality 97\n"
            "  .png          →  Lossless PNG\n"
            "  .tif / .tiff  →  16-bit TIFF  (best for astro post-processing)")
        bo = QPushButton("💾  Save as"); tip(bo, "Choose output path"); bo.clicked.connect(self._browse_output)
        ro = QHBoxLayout(); ro.addWidget(QLabel("Output:")); ro.addWidget(self._out, 1); ro.addWidget(bo); lay.addLayout(ro)

        self._dark = QLineEdit()
        self._dark.setPlaceholderText("Optional: folder of dark calibration frames…")
        tip(self._dark,
            "Dark frames (same ISO/gain, exposure, temperature).\n"
            "Median-stacked into a master dark and subtracted from every light.")
        bd = QPushButton("🌑  Dark folder"); tip(bd, "Select dark calibration folder"); bd.clicked.connect(self._browse_dark)
        rd = QHBoxLayout(); rd.addWidget(QLabel("Darks:")); rd.addWidget(self._dark, 1); rd.addWidget(bd); lay.addLayout(rd)
        return box

    # ── Tabs ──────────────────────────────────────────────────────────────────
    def _build_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.addTab(self._tab_stacking(),    "⚗  Stacking")
        tabs.addTab(self._tab_alignment(),   "🎯  Alignment")
        tabs.addTab(self._tab_video_ser(),   "🎬  Video / SER")
        tabs.addTab(self._tab_postprocess(), "✨  Post-Process")
        tabs.addTab(self._tab_quickstack(),  "⚡  Quick Stack")
        tabs.addTab(self._tab_advanced(),    "⚙  Advanced")
        tabs.tabBar().setTabTextColor(4, QColor(C["warning"]))
        return tabs

    # ── Stacking tab ──────────────────────────────────────────────────────────
    def _tab_stacking(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)
        lay.setContentsMargins(14, 14, 14, 14); lay.setSpacing(14)
        self._mode = QComboBox()
        self._mode.addItems(["average", "median", "sigma", "maximum", "minimum"])
        tip(self._mode,
            "Stacking algorithm:\n\n"
            "average  — Mean per pixel. Fast, GPU-accelerated.\n\n"
            "median   — Median per pixel. Removes hot pixels, satellites,\n"
            "           cosmic rays. Memory-intensive.\n\n"
            "sigma    — Sigma-clipping mean. Professional standard (DSS, Siril,\n"
            "           PixInsight). Best SNR for deep-sky.\n\n"
            "maximum  — Brightest pixel. Star trails, lightning, aurora.\n\n"
            "minimum  — Darkest pixel. Background/gradient removal.")
        self._mode.currentTextChanged.connect(self._on_mode_changed)
        lay.addLayout(labeled_row("Stack mode:", self._mode, label_width=130))

        self._sigma_box = QGroupBox("Sigma-Clipping Settings")
        sg = QGridLayout(self._sigma_box); sg.setSpacing(10)
        self._sig_lo = QDoubleSpinBox(); self._sig_lo.setRange(0.5,10); self._sig_lo.setSingleStep(0.5); self._sig_lo.setValue(2.0)
        tip(self._sig_lo, "Reject pixels below  mean − σ_low × std_dev  (typical: 1.5–3.0)")
        self._sig_hi = QDoubleSpinBox(); self._sig_hi.setRange(0.5,10); self._sig_hi.setSingleStep(0.5); self._sig_hi.setValue(2.0)
        tip(self._sig_hi, "Reject pixels above  mean + σ_high × std_dev  (typical: 1.5–3.0)")
        self._sig_it = QSpinBox(); self._sig_it.setRange(1,10); self._sig_it.setValue(3)
        tip(self._sig_it, "Sigma-clipping iterations. 2–5 typical. Diminishing returns above 5.")
        sg.addWidget(QLabel("σ low:"),      0, 0); sg.addWidget(self._sig_lo, 0, 1)
        sg.addWidget(QLabel("σ high:"),     0, 2); sg.addWidget(self._sig_hi, 0, 3)
        sg.addWidget(QLabel("Iterations:"), 1, 0); sg.addWidget(self._sig_it, 1, 1)
        lay.addWidget(self._sigma_box); self._sigma_box.setVisible(False)

        self._stitch = QCheckBox("Stitch stacked groups into panorama")
        tip(self._stitch, "Stitch all groups into a panorama after stacking.\nRequires ≥20–30% overlap. Ignored for video/SER.")
        lay.addWidget(self._stitch)

        self._thresh = QSpinBox(); self._thresh.setRange(5,500); self._thresh.setValue(20)
        tip(self._thresh, "Min SIFT matches to group two images together.\nHigher = stricter grouping.")
        lay.addLayout(labeled_row("SIFT group threshold:", self._thresh, label_width=175))
        lay.addStretch(); return w

    # ── Alignment tab ─────────────────────────────────────────────────────────
    def _tab_alignment(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)
        lay.setContentsMargins(14,14,14,14); lay.setSpacing(14)
        self._align = QComboBox()
        self._align.addItems(["none", "orb", "ecc"])
        tip(self._align,
            "Alignment method:\n\n"
            "none  — No alignment (pre-aligned or tracked mount).\n\n"
            "orb   — ORB + RANSAC. Fast, robust. Good for most targets.\n\n"
            "ecc   — Sub-pixel accuracy. Best for star fields / deep-sky.\n"
            "        Falls back to ORB if convergence fails.")
        lay.addLayout(labeled_row("Alignment:", self._align, label_width=130))
        lay.addWidget(h_line()); lay.addWidget(section_label("ORB Settings"))
        self._orb_feat = QSpinBox(); self._orb_feat.setRange(500,20000); self._orb_feat.setSingleStep(500); self._orb_feat.setValue(5000)
        tip(self._orb_feat, "Max ORB keypoints per image.\n2000–5000: fast.  5000–10000: better for low-contrast.")
        lay.addLayout(labeled_row("Max features:", self._orb_feat, label_width=130))
        info = QLabel("ℹ  ECC: Euclidean motion, 200 iterations, 1e-7 precision.\n   Falls back to ORB if convergence fails.")
        info.setStyleSheet(f"color:{C['text_dim']}; font-size:12px;"); info.setWordWrap(True)
        lay.addWidget(info); lay.addStretch(); return w

    # ── Video/SER tab ─────────────────────────────────────────────────────────
    def _tab_video_ser(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)
        lay.setContentsMargins(14,14,14,14); lay.setSpacing(14)
        lay.addWidget(section_label("Frame Selection"))
        self._skip = QSpinBox(); self._skip.setRange(1,100); self._skip.setValue(1)
        tip(self._skip, "Use every Nth frame.\nskip=1 → all  |  skip=2 → 50%  |  skip=5 → 20%")
        lay.addLayout(labeled_row("Frame skip (every Nth):", self._skip, label_width=185))
        self._maxf = QSpinBox(); self._maxf.setRange(0,100000); self._maxf.setValue(0)
        self._maxf.setSpecialValueText("∞  unlimited")
        tip(self._maxf, "Stop after N frames. 0 = unlimited.\nPlanetary SER: best-frame count is typically 10–30% of total.")
        lay.addLayout(labeled_row("Max frames (0=all):", self._maxf, label_width=185))
        lay.addWidget(h_line())
        ser = QLabel("SER format supports:\n  🪐  Planetary  •  🌙  Lunar  •  ☀  Solar\n\n"
                     "Handles:\n  • 8-bit & 16-bit depths\n  • All Bayer patterns\n"
                     "  • RGB / BGR / Mono\n\nRecommended:\n"
                     "  Mode: sigma  |  Align: orb  |  Stretch: ✓  |  Hot px: 30")
        ser.setStyleSheet(f"color:{C['text_dim']}; font-size:13px;"); ser.setWordWrap(True)
        lay.addWidget(ser); lay.addStretch(); return w

    # ── Post-Process tab ──────────────────────────────────────────────────────
    def _tab_postprocess(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)
        lay.setContentsMargins(14,14,14,14); lay.setSpacing(14)
        self._enhance = QCheckBox("Denoise + Sharpen (unsharp mask)")
        self._enhance.setChecked(True)
        tip(self._enhance,
            "Post-processing steps applied to the final image:\n\n"
            "1. fastNlMeansDenoisingColored  (h=5, hColor=5)\n"
            "2. Unsharp mask via Laplacian kernel\n\n"
            "Disable to apply your own post-processing downstream.")
        lay.addWidget(self._enhance)
        self._stretch = QCheckBox("Auto histogram stretch")
        tip(self._stretch, "Remap 0.5th–99.5th percentile to 0–255 per channel.\nReveals faint detail in deep-sky / SER captures.")
        lay.addWidget(self._stretch)
        lay.addWidget(h_line()); lay.addWidget(section_label("Hot Pixel Removal"))
        self._hotpx = QSpinBox(); self._hotpx.setRange(0,255); self._hotpx.setValue(0)
        self._hotpx.setSpecialValueText("0  (disabled)")
        tip(self._hotpx, "Replace pixels > threshold from 3×3 median.\n0=off  |  20–40=CMOS  |  50–80=aggressive")
        lay.addLayout(labeled_row("Hot pixel threshold:", self._hotpx, label_width=175))
        lay.addWidget(h_line())
        fmt = QLabel("Output format set by extension:\n\n"
                     "  .jpg / .jpeg  →  JPEG quality 97  (smallest)\n"
                     "  .png          →  Lossless PNG\n"
                     "  .tif / .tiff  →  16-bit TIFF  (best for PixInsight / Siril)")
        fmt.setStyleSheet(f"color:{C['text_dim']}; font-size:13px;"); fmt.setWordWrap(True)
        lay.addWidget(fmt); lay.addStretch(); return w

    # ── Quick Stack tab ───────────────────────────────────────────────────────
    def _tab_quickstack(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)
        lay.setContentsMargins(14,14,14,14); lay.setSpacing(12)
        self._lite = QCheckBox("Enable Quick Stack mode")
        self._lite.setStyleSheet(f"font-size:15px; font-weight:700; color:{C['warning']};")
        tip(self._lite,
            "Quick Stack overrides all Stacking / Alignment / Post-Process settings.\n\n"
            "Pipeline: load → optional ORB align → fast average → save.\n"
            "No SIFT grouping, no denoising, no stretch, no dark subtraction.\n\n"
            "Ideal for: CPU machines, quick previews, burst photos, large video/SER.")
        lay.addWidget(self._lite); lay.addWidget(h_line())
        card = QLabel(
            "⚡  Quick Stack  —  Maximum Speed, Minimum Resources\n\n"
            "Skips SIFT grouping (the slowest step) and uses a fast\n"
            "incremental mean stack. ORB alignment is optional.\n\n"
            "Typical speed vs Full pipeline (20 × 6 MP images, CPU):\n\n"
            "   Full pipeline   ≈  40–60 s\n"
            "   Quick Stack     ≈   3–6 s\n\n"
            "Use for a fast preview, then run the full pipeline for quality output.")
        card.setWordWrap(True)
        card.setStyleSheet(
            f"color:{C['text_dim']}; font-size:13px;"
            f"background:{C['surface2']}; border:1px solid {C['border']};"
            f"border-radius:8px; padding:14px;")
        lay.addWidget(card); lay.addWidget(section_label("Quick Stack Options"))
        self._lite_no_align = QCheckBox("Skip alignment entirely  (pure average — fastest)")
        tip(self._lite_no_align, "Skip ORB alignment.\nUse only when images are pre-aligned (tracked mount, fixed tripod).")
        lay.addWidget(self._lite_no_align)
        self._lite_fmt = QComboBox(); self._lite_fmt.addItems(["jpg", "png", "tif"])
        tip(self._lite_fmt, "Output format for Quick Stack.\njpg: fastest for previews  |  tif: 16-bit lossless")
        lay.addLayout(labeled_row("Output format:", self._lite_fmt, label_width=145))
        lay.addStretch(); return w

    # ── Advanced tab ──────────────────────────────────────────────────────────
    def _tab_advanced(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)
        lay.setContentsMargins(14,14,14,14); lay.setSpacing(14)
        self._nogpu = QCheckBox("Force CPU  (disable GPU acceleration)")
        tip(self._nogpu, "Force CPU even if GPU is available.\nUse when VRAM is insufficient or for reproducible results.")
        lay.addWidget(self._nogpu)
        lay.addWidget(h_line()); lay.addWidget(section_label("Memory / Batch Sizing"))
        mem = QLabel("UltraStack auto-estimates a safe GPU batch size (70% of VRAM).\n"
                     "For large images or limited VRAM it uses incremental stacking.\n\n"
                     "If you get CUDA out-of-memory:\n"
                     "  1. Enable 'Force CPU'\n  2. Use average or sigma mode\n  3. Increase frame skip")
        mem.setStyleSheet(f"color:{C['text_dim']}; font-size:13px;"); mem.setWordWrap(True)
        lay.addWidget(mem)
        lay.addWidget(h_line()); lay.addWidget(section_label("Dependencies"))
        dep = QLabel("Required:\n  pip install opencv-contrib-python numpy torch tqdm PyQt5\n\n"
                     "Optional (FITS support):\n  pip install astropy\n\n"
                     "GPU: pytorch.org → Get Started → select your CUDA version")
        dep.setStyleSheet(f"color:{C['text_dim']}; font-size:12px;"
                          "font-family:'Cascadia Code','Fira Code','Consolas',monospace;")
        dep.setWordWrap(True); lay.addWidget(dep); lay.addStretch(); return w

    # ── Right panel ───────────────────────────────────────────────────────────
    def _build_right(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 14, 14, 14); lay.setSpacing(8)
        ph = QHBoxLayout(); ph.addWidget(section_label("Processing Log")); ph.addStretch()
        clr = QPushButton("⌫  Clear"); clr.setFixedWidth(88)
        tip(clr, "Clear the processing log"); clr.clicked.connect(lambda: self._console.clear())
        ph.addWidget(clr); lay.addLayout(ph)
        self._console = QTextEdit()
        self._console.setObjectName("console"); self._console.setReadOnly(True)
        self._console.setLineWrapMode(QTextEdit.WidgetWidth); lay.addWidget(self._console, 1)
        self._progress = QProgressBar(); self._progress.setRange(0, 0)
        self._progress.setVisible(False); lay.addWidget(self._progress)

        # System log panel (hidden until needed)
        self._syslog_panel = QWidget(); self._syslog_panel.setVisible(False)
        sl = QVBoxLayout(self._syslog_panel); sl.setContentsMargins(0, 6, 0, 0); sl.setSpacing(4)
        sh = QHBoxLayout(); sh.addWidget(section_label("⚙  System / Diagnostics")); sh.addStretch()
        self._sys_toggle = QPushButton("▲  Hide"); self._sys_toggle.setFixedWidth(82)
        self._sys_toggle.setStyleSheet(
            f"font-size:11px; padding:3px 8px; color:{C['text_dim']};"
            f"background:transparent; border:1px solid {C['border']}; border-radius:5px;")
        tip(self._sys_toggle, "Toggle system diagnostics panel.\nShows GPU probe results and non-critical messages.")
        self._sys_toggle.clicked.connect(self._toggle_syslog)
        sh.addWidget(self._sys_toggle); sl.addLayout(sh)
        self._syslog_body = QTextEdit(); self._syslog_body.setObjectName("syslog")
        self._syslog_body.setReadOnly(True); self._syslog_body.setFixedHeight(115)
        self._syslog_body.setLineWrapMode(QTextEdit.WidgetWidth); sl.addWidget(self._syslog_body)
        lay.addWidget(self._syslog_panel); return w

    def _toggle_syslog(self):
        vis = self._syslog_body.isVisible()
        self._syslog_body.setVisible(not vis)
        self._sys_toggle.setText("▼  Show" if vis else "▲  Hide")

    def _sys_append(self, text: str, colour: str):
        e = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        self._syslog_body.moveCursor(QTextCursor.End)
        self._syslog_body.insertHtml(f'<span style="color:{colour}; font-size:12px;">{e}</span><br>')
        self._syslog_body.moveCursor(QTextCursor.End)

    # ── Bottom bar ────────────────────────────────────────────────────────────
    def _build_bottom_bar(self) -> QWidget:
        bar = QWidget(); bar.setFixedHeight(72)
        bar.setStyleSheet(f"background:{C['surface']}; border-top:1px solid {C['border']};")
        lay = QHBoxLayout(bar); lay.setContentsMargins(22, 0, 22, 0); lay.setSpacing(12)
        self._type_lbl = QLabel("No input selected")
        self._type_lbl.setStyleSheet(f"color:{C['text_dim']}; font-size:13px;")
        lay.addWidget(self._type_lbl); lay.addStretch()
        self._stop_btn = QPushButton("⬛  Stop"); self._stop_btn.setObjectName("danger")
        self._stop_btn.setFixedSize(110, 46); self._stop_btn.setVisible(False)
        tip(self._stop_btn, "Abort the current job.\nPartial output may not be saved.")
        self._stop_btn.clicked.connect(self._stop_job); lay.addWidget(self._stop_btn)
        self._run_btn = WaveRunButton("▶   Run UltraStack")
        tip(self._run_btn,
            "Start the stacking pipeline.\nRuns in background — UI stays responsive.\n\n"
            "Enable ⚡ Quick Stack tab for fast CPU-optimised preview.")
        self._run_btn.clicked.connect(self._run_job); lay.addWidget(self._run_btn)
        return bar

    # ── Handlers ──────────────────────────────────────────────────────────────
    def _on_mode_changed(self, m: str): self._sigma_box.setVisible(m == "sigma")
    def _on_drop(self, path: str):      self._inp.setText(path)

    def _on_input_changed(self, text: str):
        if not text: self._type_lbl.setText("No input selected"); return
        p = Path(text)
        if   p.is_dir():                       self._type_lbl.setText(f"📁  Folder  —  {p.name}")
        elif p.suffix.lower() == ".ser":       self._type_lbl.setText(f"🔭  SER  —  {p.name}")
        elif p.suffix.lower() in {".mp4",".avi",".mov",".mkv",".wmv",".webm"}:
                                               self._type_lbl.setText(f"🎬  Video  —  {p.name}")
        else:                                  self._type_lbl.setText(f"📄  {p.name}")

    def _browse_input(self):
        d = QFileDialog.getExistingDirectory(self, "Select image folder")
        if d: self._inp.setText(d); return
        f, _ = QFileDialog.getOpenFileName(
            self, "Select video or SER file", "",
            "Supported (*.mp4 *.avi *.mov *.mkv *.wmv *.webm *.m4v *.ser);;"
            "Video (*.mp4 *.avi *.mov *.mkv *.wmv *.webm *.m4v);;SER (*.ser);;All (*)")
        if f: self._inp.setText(f)

    def _browse_output(self):
        f, _ = QFileDialog.getSaveFileName(
            self, "Save stacked output", "stacked_output.tif",
            "TIFF 16-bit (*.tif *.tiff);;PNG (*.png);;JPEG (*.jpg *.jpeg);;All (*)")
        if f: self._out.setText(f)

    def _browse_dark(self):
        d = QFileDialog.getExistingDirectory(self, "Select dark frames folder")
        if d: self._dark.setText(d)

    # ── Job control ───────────────────────────────────────────────────────────
    def _run_job(self):
        if not ULTRASTACK_AVAILABLE:
            QMessageBox.critical(self, "Import Error",
                f"Cannot import ultrastack.py:\n\n{_IMPORT_ERROR}\n\n"
                "Ensure ultrastack.py is in the same folder."); return
        inp = self._inp.text().strip()
        if not inp:
            QMessageBox.warning(self, "No input", "Please specify an input."); return
        out = self._out.text().strip()
        if not out:
            ts = datetime.now().strftime("%m%d_%H%M%S")
            out = f"ultrastack_{ts}.tif"; self._out.setText(out)
        max_f = self._maxf.value(); lite = self._lite.isChecked()
        cfg = dict(
            input=inp, output=out, dark=self._dark.text().strip() or None,
            mode=self._mode.currentText(), align=self._align.currentText(),
            enhance=self._enhance.isChecked(), stretch=self._stretch.isChecked(),
            stitch=self._stitch.isChecked(), hot_pixels=self._hotpx.value(),
            skip=self._skip.value(), max_frames=max_f if max_f > 0 else None,
            threshold=self._thresh.value(), sigma_low=self._sig_lo.value(),
            sigma_high=self._sig_hi.value(), sigma_iters=self._sig_it.value(),
            lite=lite, lite_skip_align=self._lite_no_align.isChecked(),
            lite_fmt=self._lite_fmt.currentText().split()[0],
            _device=self._device, _torch=self._torch,
        )
        if self._nogpu.isChecked(): cfg["_device"] = "cpu"; cfg["_torch"] = None
        self._console.clear()
        self._log(f"Starting  [{'⚡ Quick Stack' if lite else 'Full Pipeline'}]  "
                  f"—  {datetime.now().strftime('%H:%M:%S')}")
        self._run_btn.setEnabled(False); self._stop_btn.setVisible(True)
        self._progress.setVisible(True)
        self._worker = WorkerThread(cfg)
        self._worker.log_line.connect(self._log)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
        self.statusBar().showMessage("  Processing…  see log on the right.")

    def _stop_job(self):
        if self._worker: self._worker.terminate(); self._log("  ⬛  Aborted.")
        self._on_finished(False, "Aborted")

    def _on_finished(self, ok: bool, msg: str):
        self._run_btn.setEnabled(True); self._stop_btn.setVisible(False)
        self._progress.setVisible(False)
        if ok:
            self._log(f"\n  ✓  DONE — saved to: {msg}")
            self.statusBar().showMessage(f"  ✓  Saved: {msg}")
            QMessageBox.information(self, "Complete", f"✓  Stacking complete!\n\nSaved to:\n{msg}")
        else:
            self._log(f"\n  ✗  Failed: {msg}")
            self.statusBar().showMessage(f"  ✗  Failed: {msg}")

    # ── Log renderer ──────────────────────────────────────────────────────────
    def _log(self, text: str):
        t = text.strip()
        e = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        m = re.search(r"─+\s*(STEP\s*\d+.*?)\s*─+", t)
        if m or ("STEP" in t and "──" in t):
            label = (m.group(1).strip() if m else t)
            label = label.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            html = (f'<div style="text-align:center; margin:5px 0;">'
                    f'<span style="color:{C["border_hi"]};">─────  </span>'
                    f'<span style="color:{C["accent2"]}; font-weight:bold;">{label}</span>'
                    f'<span style="color:{C["border_hi"]};">  ─────</span></div>')
        elif t.startswith("═") or (len(t) > 4 and all(c in "═─" for c in t)):
            html = f'<div style="color:{C["border_hi"]}; font-size:11px;">{e}</div>'
        elif t.startswith("✓") or "DONE" in t:
            html = f'<span style="color:{C["success"]}; font-weight:bold;">{e}</span><br>'
        elif t.startswith("⚡"):
            html = f'<span style="color:{C["warning"]}; font-weight:bold;">{e}</span><br>'
        elif t.startswith("⚠") or "warn" in t.lower():
            html = f'<span style="color:{C["warning"]};">{e}</span><br>'
        elif t.startswith("✗") or "error" in t.lower() or "failed" in t.lower():
            html = f'<span style="color:{C["danger"]}; font-weight:bold;">{e}</span><br>'
        elif t.startswith("Starting") or t.startswith("UltraStack"):
            html = f'<span style="color:{C["accent"]}; font-weight:bold;">{e}</span><br>'
        else:
            html = f'<span style="color:{C["text"]};">{e}</span><br>'
        self._console.moveCursor(QTextCursor.End)
        self._console.insertHtml(html)
        self._console.moveCursor(QTextCursor.End)

    # ── About ─────────────────────────────────────────────────────────────────
    def _show_about(self):
        QMessageBox.about(self, "About UltraStack",
            f"<b>UltraStack v2</b><br>"
            f"GPU-Accelerated Astronomical Image Stacking<br><br>"
            f"Stack image folders, video files, or SER captures<br>"
            f"using Average / Median / Sigma / Max / Min modes.<br>"
            f"<b>⚡ Quick Stack</b> mode for fast CPU-optimised previews.<br><br>"
            f"<hr>"
            f"<b>Developer:</b>  {DEV_NAME}<br>"
            f"<b>Email:</b>  <a href='mailto:{DEV_EMAIL}'>{DEV_EMAIL}</a><br>"
            f"<b>GitHub:</b>  <a href='https://{DEV_GITHUB}'>{DEV_GITHUB}</a><br><br>"
            f"<hr>"
            f"<b>Backend:</b>  ultrastack.py<br>"
            f"<b>GUI:</b>  PyQt5<br><br>"
            f"Images  : JPG, PNG, TIFF, FITS, BMP, WEBP, EXR<br>"
            f"Video   : MP4, AVI, MOV, MKV, WMV, WEBM, M4V, TS<br>"
            f"Astro   : SER (all Bayer / Mono / RGB / BGR, 8 & 16-bit)")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    QToolTip.setFont(QFont("Segoe UI", 11))
    app.setStyleSheet(STYLESHEET)
    win = UltraStackGUI()
    # win.show() is called inside UltraStackGUI after the splash completes
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
