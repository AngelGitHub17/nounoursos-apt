"""NounoursUI — socle visuel commun des applications NounoursOS.

Couleurs, feuille de style, petits widgets (cartes, lignes de réglage,
interrupteurs, boutons) et utilitaires système partagés par :
  - nounoursos-parametres   (Paramètres)
  - nounoursos-bienvenue    (assistant de bienvenue / OOBE)
  - nounoursos-maj          (Mise à jour de NounoursOS)
"""
import configparser
import os
import pwd
import shlex
import shutil
import subprocess

from PyQt6.QtCore import (Qt, QSize, QRectF, QPropertyAnimation, QEasingCurve,
                          pyqtProperty, pyqtSignal, QPointF)
from PyQt6.QtGui import (QColor, QFont, QIcon, QPainter, QPixmap, QPainterPath,
                         QLinearGradient, QBrush, QPen)
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QWidget, QSizePolicy, QAbstractButton)

# --------------------------------------------------------------------------
# Chemins (surchargeables pour tester hors d'un vrai NounoursOS)
# --------------------------------------------------------------------------
ROOT = os.environ.get("NOUNOURSOS_ROOT", "")          # préfixe de test
DATA = ROOT + "/usr/share/nounoursos"
LNF = ROOT + "/usr/share/plasma/look-and-feel"
WALLPAPERS = ROOT + "/usr/share/wallpapers"
HELPER = "/usr/libexec/nounoursos/nounoursos-root-helper"
CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "nounoursos")
CACHE_DIR = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "nounoursos")
DEMO = os.environ.get("NOUNOURSOS_DEMO") == "1"     # données fictives (tests, captures)

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------
HONEY = "#C9864B"        # caramel : couleur principale
HONEY_HOVER = "#B8733D"
HONEY_LIGHT = "#F3B562"  # miel
NIGHT = "#1F1A2E"
PLUM = "#3B2A4F"

LIGHT = dict(bg="#F6F2EE", side="#EFE9E3", card="#FFFFFF", border="#E6DED6",
             text="#2B1D3A", sub="#7A6E7E", hover="#F3ECE5", sel=HONEY,
             seltext="#FFFFFF", field="#FFFFFF")
DARK = dict(bg="#1C1825", side="#221D2D", card="#2A2436", border="#3A3247",
            text="#F4EFF7", sub="#A79FB0", hover="#332C40", sel=HONEY,
            seltext="#FFFFFF", field="#2A2436")

ACCENTS = [("Miel", "#C9864B"), ("Bleu", "#3D7EDB"), ("Violet", "#7E57C2"),
           ("Rose", "#D9568C"), ("Vert", "#3FA36B"), ("Graphite", "#6B6478")]


def is_dark():
    """Thème sombre si le schéma de couleurs KDE actif est sombre."""
    if os.environ.get("NOUNOURSOS_THEME") in ("dark", "light"):
        return os.environ["NOUNOURSOS_THEME"] == "dark"
    cfg = configparser.ConfigParser(strict=False, interpolation=None)
    try:
        cfg.read(os.path.expanduser("~/.config/kdeglobals"))
        return "dark" in cfg.get("General", "ColorScheme", fallback="").lower()
    except Exception:
        return False


def colors():
    return DARK if is_dark() else LIGHT


def stylesheet(c=None, scoped=False):
    qss = _stylesheet(c or colors())
    return _scope(qss) if scoped else qss


# Conteneurs NounoursOS : le style ne s'applique qu'à l'intérieur (pas aux modules KDE)
_SCOPES = ("#Sidebar", "#NPage", "#Card")
_KEEP = ("QMainWindow", "QDialog", "#Page", "#Sidebar", "#Card", "QToolTip", "QScrollArea")


def _scope(qss):
    out = []
    for block in qss.split("}"):
        if "{" not in block:
            continue
        sel, body = block.split("{", 1)
        new = []
        for one in (x.strip() for x in sel.split(",")):
            if not one:
                continue
            if one.startswith(_KEEP):
                new.append(one)
            else:
                new.extend(f"{scope} {one}" for scope in _SCOPES)
        out.append(", ".join(new) + " {" + body + "}")
    return "\n".join(out)


def _stylesheet(c):
    return f"""
    * {{ font-family: "Noto Sans", "DejaVu Sans", sans-serif; color: {c['text']}; }}
    QMainWindow, QDialog, #Page {{ background: {c['bg']}; }}
    QLabel {{ background: transparent; }}
    QLabel[role="title"]    {{ font-size: 22pt; font-weight: 700; }}
    QLabel[role="h1"]       {{ font-size: 17pt; font-weight: 700; }}
    QLabel[role="h2"]       {{ font-size: 11pt; font-weight: 700; }}
    QLabel[role="sub"]      {{ color: {c['sub']}; font-size: 10pt; }}
    QLabel[role="section"]  {{ color: {c['sub']}; font-size: 9pt; font-weight: 600;
                               padding: 10px 6px 2px 6px; }}
    #Card {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 14px; }}
    #Sidebar {{ background: {c['side']}; border-right: 1px solid {c['border']}; }}
    QLineEdit {{ background: {c['field']}; border: 1px solid {c['border']}; border-radius: 9px;
                 padding: 7px 10px; font-size: 10pt; selection-background-color: {HONEY}; }}
    QLineEdit:focus {{ border: 2px solid {HONEY}; padding: 6px 9px; }}
    QPushButton {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 9px;
                   padding: 8px 16px; font-size: 10pt; }}
    QPushButton:hover {{ background: {c['hover']}; }}
    QPushButton[role="primary"] {{ background: {HONEY}; color: white; border: none; font-weight: 600; }}
    QPushButton[role="primary"]:hover {{ background: {HONEY_HOVER}; }}
    QPushButton[role="primary"]:disabled {{ background: {c['border']}; color: {c['sub']}; }}
    QPushButton[role="link"] {{ background: transparent; border: none; color: {HONEY}; padding: 4px; }}
    QPushButton[role="link"]:hover {{ text-decoration: underline; }}
    QProgressBar {{ background: {c['border']}; border: none; border-radius: 4px; height: 8px;
                    max-height: 8px; text-align: center; color: transparent; }}
    QProgressBar::chunk {{ background: {HONEY}; border-radius: 4px; }}
    QSlider::groove:horizontal {{ height: 4px; background: {c['border']}; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: {HONEY}; border-radius: 2px; }}
    QSlider::handle:horizontal {{ background: white; border: 1px solid {c['border']};
                                  width: 18px; height: 18px; margin: -8px 0; border-radius: 9px; }}
    QScrollArea {{ background: transparent; border: none; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 4px; min-height: 30px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    QListWidget {{ background: transparent; border: none; outline: none; font-size: 10pt; }}
    QListWidget::item {{ padding: 6px 8px; border-radius: 8px; margin: 1px 4px; }}
    QListWidget::item:hover {{ background: {c['hover']}; }}
    QListWidget::item:selected {{ background: {c['sel']}; color: {c['seltext']}; }}
    QToolTip {{ background: {c['card']}; color: {c['text']}; border: 1px solid {c['border']}; }}
    """


def label(text, role=None, wrap=False, align=None):
    lbl = QLabel(text)
    if role:
        lbl.setProperty("role", role)
    if wrap:
        lbl.setWordWrap(True)
    if align is not None:
        lbl.setAlignment(align)
    return lbl


def button(text, role=None, slot=None):
    b = QPushButton(text)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if role:
        b.setProperty("role", role)
    if slot:
        b.clicked.connect(slot)
    return b


# --------------------------------------------------------------------------
# Icônes
# --------------------------------------------------------------------------
def logo_pixmap(size):
    for path in (DATA + "/logo-256.png", "/usr/share/icons/hicolor/256x256/apps/nounoursos.png"):
        if os.path.exists(path):
            return QPixmap(path).scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
    return QIcon.fromTheme("nounoursos").pixmap(size, size)


def tile_icon(icon_name, color, size=28, glyph=None):
    """Icône façon macOS : carré arrondi coloré avec pictogramme blanc."""
    dpr = 2
    pm = QPixmap(size * dpr, size * dpr)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QLinearGradient(0, 0, 0, size)
    base = QColor(color)
    grad.setColorAt(0, base.lighter(115))
    grad.setColorAt(1, base)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size, size), size * 0.24, size * 0.24)
    p.fillPath(path, QBrush(grad))
    inner = int(size * 0.62)
    off = (size - inner) / 2
    icon = QIcon.fromTheme(icon_name + "-symbolic") if icon_name else QIcon()
    if icon.isNull() and icon_name:
        icon = QIcon.fromTheme(icon_name)
    if not icon.isNull():
        glyph_pm = icon.pixmap(QSize(inner * dpr, inner * dpr))
        white = QPixmap(glyph_pm.size())
        white.fill(Qt.GlobalColor.transparent)
        gp = QPainter(white)
        gp.drawPixmap(0, 0, glyph_pm)
        gp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        gp.fillRect(white.rect(), QColor("white"))
        gp.end()
        p.drawPixmap(QRectF(off, off, inner, inner), white, QRectF(white.rect()))
    else:  # pas de thème d'icônes : lettre
        p.setPen(QColor("white"))
        f = QFont("Noto Sans", int(size * 0.42))
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, glyph or "•")
    p.end()
    return pm


def badge_pixmap(count, size=20):
    dpr = 2
    pm = QPixmap(size * dpr, size * dpr)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#E5484D"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(0, 0, size, size))
    p.setPen(QColor("white"))
    f = QFont("Noto Sans", 8)
    f.setBold(True)
    p.setFont(f)
    p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, str(count))
    p.end()
    return pm


# --------------------------------------------------------------------------
# Widgets
# --------------------------------------------------------------------------
class Card(QFrame):
    """Bloc arrondi blanc contenant des lignes séparées par un filet."""

    def __init__(self, parent=None, margins=(0, 0, 0, 0)):
        super().__init__(parent)
        self.setObjectName("Card")
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(*margins)
        self.lay.setSpacing(0)
        self._rows = 0

    def add(self, w):
        if self._rows:
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background: {colors()['border']}; margin: 0 14px;")
            self.lay.addWidget(sep)
        self.lay.addWidget(w)
        self._rows += 1
        return w


class Toggle(QAbstractButton):
    """Interrupteur on/off façon macOS, animé."""

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(44, 26)
        self._pos = 1.0 if checked else 0.0
        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animate)

    def _animate(self, on):
        self._anim.stop()
        self._anim.setEndValue(1.0 if on else 0.0)
        self._anim.start()

    def getPos(self):
        return self._pos

    def setPos(self, v):
        self._pos = v
        self.update()

    pos = pyqtProperty(float, getPos, setPos)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        off = QColor(colors()["border"])
        on = QColor(HONEY)
        r = self._pos
        track = QColor(int(off.red() + (on.red() - off.red()) * r),
                       int(off.green() + (on.green() - off.green()) * r),
                       int(off.blue() + (on.blue() - off.blue()) * r))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0, 0, 44, 26), 13, 13)
        p.setBrush(QColor("white"))
        p.drawEllipse(QPointF(13 + 18 * r, 13), 10, 10)


class SettingRow(QFrame):
    """Ligne de réglage : [icône] Titre / sous-titre ......... [widget]"""
    clicked = pyqtSignal()

    def __init__(self, title, subtitle=None, widget=None, icon=None, chevron=False):
        super().__init__()
        self.setMinimumHeight(52)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(12)
        if icon is not None:
            ic = QLabel()
            ic.setPixmap(icon)
            lay.addWidget(ic)
        texts = QVBoxLayout()
        texts.setSpacing(1)
        t = label(title)
        t.setStyleSheet("font-size: 10pt;")
        texts.addWidget(t)
        if subtitle:
            self.sub = label(subtitle, "sub", wrap=True)
            texts.addWidget(self.sub)
        lay.addLayout(texts, 1)
        if widget is not None:
            lay.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        if chevron:
            ch = label("›")
            ch.setStyleSheet(f"font-size: 16pt; color: {colors()['sub']};")
            lay.addWidget(ch)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._chevron = chevron

    def mouseReleaseEvent(self, e):
        if self._chevron and e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(e)


class ChoiceCard(QAbstractButton):
    """Grande carte sélectionnable avec image (thème, disposition…)."""

    def __init__(self, title, pixmap, parent=None, w=220, h=150):
        super().__init__(parent)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._title = title
        self._pm = pixmap
        self._w, self._h = w, h
        self.setFixedSize(w, h + 36)

    def paintEvent(self, _):
        c = colors()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = QRectF(3, 3, self._w - 6, self._h - 6)
        path = QPainterPath()
        path.addRoundedRect(rect, 12, 12)
        p.setClipPath(path)
        if self._pm and not self._pm.isNull():
            p.drawPixmap(rect, self._pm, QRectF(self._pm.rect()))
        else:
            p.fillPath(path, QColor(c["card"]))
        p.setClipping(False)
        pen = QPen(QColor(HONEY) if self.isChecked() else QColor(c["border"]))
        pen.setWidthF(3 if self.isChecked() else 1)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, 12, 12)
        f = QFont("Noto Sans", 10)
        f.setBold(self.isChecked())
        p.setFont(f)
        p.setPen(QColor(c["text"]))
        p.drawText(QRectF(0, self._h, self._w, 30), Qt.AlignmentFlag.AlignCenter, self._title)


class Swatch(QAbstractButton):
    def __init__(self, color, name):
        super().__init__()
        self.color = color
        self.setToolTip(name)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(30, 30)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.isChecked():
            p.setPen(QPen(QColor(self.color), 2))
            p.drawEllipse(QRectF(1, 1, 28, 28))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self.color))
        p.drawEllipse(QRectF(5, 5, 20, 20))


def hline():
    f = QFrame()
    f.setFixedHeight(1)
    f.setStyleSheet(f"background: {colors()['border']};")
    return f


def spacer_h():
    w = QWidget()
    w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return w


# --------------------------------------------------------------------------
# Système
# --------------------------------------------------------------------------
def run(cmd, timeout=20):
    """Lance une commande et renvoie sa sortie (chaîne vide si échec)."""
    if DEMO:
        return ""
    try:
        return subprocess.run(cmd if isinstance(cmd, list) else shlex.split(cmd),
                              capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def spawn(cmd):
    """Lance une commande en arrière-plan, sans attendre."""
    if DEMO:
        print("[demo] spawn:", cmd)
        return
    try:
        subprocess.Popen(cmd if isinstance(cmd, list) else shlex.split(cmd),
                         start_new_session=True)
    except Exception as e:
        print("Impossible de lancer", cmd, e)


def has(cmd):
    return shutil.which(cmd) is not None


def open_kcm(kcm):
    """Ouvre un module de réglage KDE seul, sans la grosse fenêtre de KDE."""
    if has("kcmshell6"):
        spawn(["kcmshell6", kcm])
    else:
        spawn(["systemsettings", kcm])


def root_helper(*args):
    """Action administrateur (demande le mot de passe via polkit)."""
    if DEMO:
        print("[demo] root-helper", args)
        return True
    return subprocess.run(["pkexec", HELPER, *args]).returncode == 0


def user_info():
    p = pwd.getpwuid(os.getuid())
    full = (p.pw_gecos or "").split(",")[0] or p.pw_name
    return p.pw_name, full


def os_release():
    info = {}
    for path in (ROOT + "/etc/os-release", "/etc/os-release"):
        try:
            with open(path) as f:
                for line in f:
                    if "=" in line:
                        k, v = line.rstrip("\n").split("=", 1)
                        info[k] = v.strip('"')
            break
        except OSError:
            continue
    if DEMO or info.get("ID") != "nounoursos":
        info.update(NAME="NounoursOS", VERSION_ID="1.0", NOUNOURSOS_CODENAME="Guimauve",
                    DEBIAN_CODENAME="trixie")
    return info


def read_conf(name, defaults):
    cfg = configparser.ConfigParser()
    cfg["main"] = defaults
    cfg.read(["/etc/nounoursos/" + name, os.path.join(CONFIG_DIR, name)])
    return cfg["main"]


def write_conf(name, values):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    cfg = configparser.ConfigParser()
    path = os.path.join(CONFIG_DIR, name)
    cfg.read(path)
    if "main" not in cfg:
        cfg["main"] = {}
    for k, v in values.items():
        cfg["main"][k] = str(v)
    with open(path, "w") as f:
        cfg.write(f)


def apply_color_scheme(dark, accent=None):
    scheme = "BreezeDark" if dark else "BreezeLight"
    cmd = ["plasma-apply-colorscheme", scheme]
    if accent:
        cmd += ["--accent-color", accent]
    spawn(cmd)


def apply_accent(accent):
    spawn(["plasma-apply-colorscheme", "--accent-color", accent])


def plasma_script(js):
    """Exécute un script Plasma (réglage des panneaux / dock)."""
    spawn(["dbus-send", "--session", "--type=method_call", "--dest=org.kde.plasmashell",
           "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", "string:" + js])
