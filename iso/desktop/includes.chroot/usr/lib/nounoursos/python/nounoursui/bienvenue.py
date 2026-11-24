"""Bienvenue dans NounoursOS — écran d'accueil en live + assistant de premier démarrage (OOBE)."""
import os
import subprocess
import sys

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPointF
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QRadialGradient, QIcon, QFont, QPixmap
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
                             QStackedWidget, QFrame, QGraphicsDropShadowEffect,
                             QGraphicsOpacityEffect, QButtonGroup, QPushButton)

from . import (label, button, logo_pixmap, Card, SettingRow, Toggle, ChoiceCard, Swatch,
               tile_icon, colors, stylesheet, spawn, root_helper, user_info, write_conf,
               apply_color_scheme, ACCENTS, HONEY, CONFIG_DIR, DEMO, LIGHT, DATA)
from .parametres import window_preview, lnf_preview

FLAG = os.path.join(CONFIG_DIR, "bienvenue-faite")
RECOMMENDED = [
    ("com.obsproject.Studio", "OBS Studio", "Streaming et enregistrement", "#302E31", "●"),
    ("com.discordapp.Discord", "Discord", "Discuter avec la communauté", "#5865F2", "D"),
    ("org.prismlauncher.PrismLauncher", "Prism Launcher", "Minecraft (serveur NSDKPlus)", "#3FA36B", "M"),
    ("com.valvesoftware.Steam", "Steam", "Jeux vidéo", "#1B2838", "S"),
    ("com.spotify.Client", "Spotify", "Musique", "#1DB954", "♪"),
    ("org.libreoffice.LibreOffice", "LibreOffice", "Bureautique", "#18A303", "L"),
    ("org.gimp.GIMP", "GIMP", "Retouche d'images", "#7E57C2", "G"),
    ("com.visualstudio.code", "Visual Studio Code", "Programmation", "#3D7EDB", "<>"),
]

GREETINGS = ["Bonjour", "Hello", "Hola", "Ciao", "Hallo", "Olá", "Merhaba", "Hej"]


def is_live():
    if os.environ.get("NOUNOURSOS_LIVE") in ("0", "1"):
        return os.environ["NOUNOURSOS_LIVE"] == "1"
    try:
        with open("/proc/cmdline") as f:
            return "boot=live" in f.read().split()
    except OSError:
        return False


class Backdrop(QWidget):
    """Fond plein écran aux couleurs du fond d'écran NounoursOS."""

    _fond = None

    def paintEvent(self, _):
        p = QPainter(self)
        r = self.rect()
        # Fond « Origami » de l'identité NounoursOS (sans ourson, la carte porte le logo)
        if Backdrop._fond is None:
            Backdrop._fond = QPixmap(os.path.join(DATA, "grub-background.png"))
        if not Backdrop._fond.isNull():
            pm = Backdrop._fond.scaled(r.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                       Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap(r.x() - (pm.width() - r.width()) // 2, r.y() - (pm.height() - r.height()) // 2, pm)
            return
        g = QLinearGradient(0, 0, r.width(), r.height())
        g.setColorAt(0, QColor("#1F1A2E"))
        g.setColorAt(0.55, QColor("#3B2A4F"))
        g.setColorAt(1, QColor("#D98A3F"))
        p.fillRect(r, g)
        glow = QRadialGradient(QPointF(r.width() * 0.8, r.height() * 0.85), r.width() * 0.55)
        glow.setColorAt(0, QColor(243, 181, 98, 120))
        glow.setColorAt(1, QColor(243, 181, 98, 0))
        p.fillRect(r, glow)


class Shell(Backdrop):
    """Fenêtre plein écran avec une carte centrale."""

    def __init__(self, card_w=820, card_h=560):
        super().__init__()
        self.setWindowTitle("Bienvenue dans NounoursOS")
        self.setWindowIcon(QIcon.fromTheme("nounoursos"))
        outer = QVBoxLayout(self)
        outer.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        self.card = QFrame()
        self.card.setObjectName("Card")
        self.card.setStyleSheet(f"#Card {{ background: {LIGHT['bg']}; border: none; border-radius: 22px; }}")
        self.card.setFixedSize(card_w, card_h)
        sh = QGraphicsDropShadowEffect(self.card)
        sh.setBlurRadius(60)
        sh.setOffset(0, 18)
        sh.setColor(QColor(0, 0, 0, 110))
        self.card.setGraphicsEffect(sh)
        row.addWidget(self.card)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch()
        self.body = QVBoxLayout(self.card)
        self.body.setContentsMargins(44, 36, 44, 30)


def fade_in(w, ms=320):
    eff = QGraphicsOpacityEffect(w)
    w.setGraphicsEffect(eff)
    a = QPropertyAnimation(eff, b"opacity", w)
    a.setDuration(ms)
    a.setStartValue(0.0)
    a.setEndValue(1.0)
    a.setEasingCurve(QEasingCurve.Type.OutCubic)
    a.finished.connect(lambda: w.setGraphicsEffect(None))
    a.start()
    w._fade = a


# ==========================================================================
# Live : Essayer ou Installer
# ==========================================================================
class BigChoice(QPushButton):
    def __init__(self, icon_name, color, glyph, title, desc, primary=False):
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(330, 190)
        bg = HONEY if primary else "#FFFFFF"
        fg = "#FFFFFF" if primary else LIGHT["text"]
        hover = "#B8733D" if primary else LIGHT["hover"]
        self.setStyleSheet(f"""
            QPushButton {{ background: {bg}; border: 1px solid {'transparent' if primary else LIGHT['border']};
                           border-radius: 18px; text-align: left; }}
            QPushButton:hover {{ background: {hover}; }}
            QLabel {{ color: {fg}; background: transparent; }}""")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        ic = QLabel()
        ic.setPixmap(tile_icon(icon_name, "#FFFFFF" if primary else color, 48, glyph)
                     if not primary else logo_pixmap(52))
        lay.addWidget(ic)
        lay.addStretch()
        t = QLabel(title)
        t.setStyleSheet("font-size: 15pt; font-weight: 700;")
        d = QLabel(desc)
        d.setWordWrap(True)
        d.setStyleSheet("font-size: 10pt;" + ("" if primary else f"color: {LIGHT['sub']};"))
        lay.addWidget(t)
        lay.addWidget(d)
        for child in (ic, t, d):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)


class LiveWelcome(Shell):
    def __init__(self):
        super().__init__(820, 560)
        b = self.body
        b.setSpacing(10)
        lg = QLabel()
        lg.setPixmap(logo_pixmap(110))
        b.addWidget(lg, 0, Qt.AlignmentFlag.AlignHCenter)
        b.addWidget(label("Bienvenue dans NounoursOS", "title", align=Qt.AlignmentFlag.AlignCenter))
        b.addWidget(label("Essayez NounoursOS sans rien modifier sur votre ordinateur, "
                          "ou installez-le dès maintenant.", "sub", wrap=True,
                          align=Qt.AlignmentFlag.AlignCenter))
        b.addSpacing(18)
        row = QHBoxLayout()
        row.setSpacing(22)
        row.addStretch()
        tryb = BigChoice("system-run", "#3B2A4F", "▶", "Essayer NounoursOS",
                         "Découvrez le système directement depuis la clé USB. Rien n'est modifié.")
        inst = BigChoice(None, HONEY, "", "Installer NounoursOS",
                         "Installez NounoursOS sur cet ordinateur en quelques minutes.", primary=True)
        tryb.clicked.connect(self.close)
        inst.clicked.connect(self.install)
        row.addWidget(tryb)
        row.addWidget(inst)
        row.addStretch()
        b.addLayout(row)
        b.addStretch()
        b.addWidget(label("Langue : Français  ·  Clavier : AZERTY  ·  Mot de passe de la session live : live",
                          "sub", align=Qt.AlignmentFlag.AlignCenter))

    def install(self):
        spawn(["nounoursos-installer"])
        self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.close()


# ==========================================================================
# Premier démarrage : assistant de configuration
# ==========================================================================
class Assistant(Shell):
    def __init__(self):
        super().__init__(860, 600)
        self.choice = {"dark": False, "accent": HONEY, "layout": "classique",
                       "auto_check": True, "auto_sec": True, "apps": set()}
        self.stack = QStackedWidget()
        self.body.addWidget(self.stack, 1)

        nav = QHBoxLayout()
        self.back = button("‹ Retour", "link", self.prev)
        self.dots = QLabel()
        self.next_b = button("Continuer", "primary", self.next)
        self.next_b.setMinimumWidth(170)
        self.next_b.setMinimumHeight(40)
        nav.addWidget(self.back)
        nav.addStretch()
        nav.addWidget(self.dots)
        nav.addStretch()
        nav.addWidget(self.next_b)
        self.body.addLayout(nav)

        for build in (self.p_hello, self.p_look, self.p_layout, self.p_apps, self.p_updates, self.p_done):
            self.stack.addWidget(build())
        self.go(0)

    # --- Navigation ---------------------------------------------------------
    def go(self, i):
        self.stack.setCurrentIndex(i)
        fade_in(self.stack.currentWidget())
        last = self.stack.count() - 1
        self.back.setVisible(0 < i < last)
        self.dots.setVisible(0 < i < last)
        self.next_b.setText({0: "Commencer", last: "C'est parti !"}.get(i, "Continuer"))
        on, off = HONEY, LIGHT["border"]
        self.dots.setText(" ".join(f"<span style='color:{on if k == i else off}; font-size:16pt'>●</span>"
                                   for k in range(1, last)))
        if i == last:
            _, full = user_info()
            self.done_title.setText(f"Tout est prêt, {full.split()[0]} !")

    def next(self):
        i = self.stack.currentIndex()
        if i == self.stack.count() - 1:
            self.finish()
        else:
            self.go(i + 1)

    def prev(self):
        self.go(max(0, self.stack.currentIndex() - 1))

    def _page(self, title, sub=None):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lay.addWidget(label(title, "title", align=Qt.AlignmentFlag.AlignCenter))
        if sub:
            lay.addWidget(label(sub, "sub", wrap=True, align=Qt.AlignmentFlag.AlignCenter))
        lay.addSpacing(14)
        return w, lay

    # --- Pages ---------------------------------------------------------------------
    def p_hello(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addStretch()
        lg = QLabel()
        lg.setPixmap(logo_pixmap(150))
        lay.addWidget(lg, 0, Qt.AlignmentFlag.AlignHCenter)
        self.greet = QLabel(GREETINGS[0])
        self.greet.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.greet.setStyleSheet(f"font-size: 48pt; font-weight: 300; color: {LIGHT['text']};")
        lay.addWidget(self.greet)
        lay.addWidget(label("Bienvenue dans NounoursOS", "sub", align=Qt.AlignmentFlag.AlignCenter))
        lay.addStretch()
        self._gi = 0
        self._geff = QGraphicsOpacityEffect(self.greet)
        self.greet.setGraphicsEffect(self._geff)
        self._gtimer = QTimer(self)
        self._gtimer.timeout.connect(self._next_greeting)
        self._gtimer.start(2200)
        return w

    def _next_greeting(self):
        if self.stack.currentIndex() != 0:
            return
        out = QPropertyAnimation(self._geff, b"opacity", self)
        out.setDuration(350)
        out.setStartValue(1.0)
        out.setEndValue(0.0)

        def swap():
            self._gi = (self._gi + 1) % len(GREETINGS)
            self.greet.setText(GREETINGS[self._gi])
            inn = QPropertyAnimation(self._geff, b"opacity", self)
            inn.setDuration(450)
            inn.setStartValue(0.0)
            inn.setEndValue(1.0)
            inn.start()
            self._ganim_in = inn
        out.finished.connect(swap)
        out.start()
        self._ganim = out

    def p_look(self):
        w, lay = self._page("Choisissez votre apparence",
                            "Clair ou sombre : NounoursOS s'adapte à vos goûts.")
        row = QHBoxLayout()
        row.addStretch()
        grp = QButtonGroup(self)
        for title, d in (("Clair", False), ("Sombre", True)):
            c = ChoiceCard(title, window_preview(d, 260, 160), w=260, h=160)
            c.setChecked(d == self.choice["dark"])
            c.clicked.connect(lambda _=False, d=d: self.choice.update(dark=d))
            grp.addButton(c)
            row.addWidget(c)
            row.addSpacing(16)
        row.addStretch()
        lay.addLayout(row)
        lay.addSpacing(12)
        lay.addWidget(label("Couleur d'accentuation", "h2", align=Qt.AlignmentFlag.AlignCenter))
        sw = QHBoxLayout()
        sw.addStretch()
        for name, col in ACCENTS:
            s = Swatch(col, name)
            s.setChecked(col == self.choice["accent"])
            s.clicked.connect(lambda _=False, col=col: self.choice.update(accent=col))
            sw.addWidget(s)
        sw.addStretch()
        lay.addLayout(sw)
        lay.addStretch()
        return w

    def p_layout(self):
        w, lay = self._page("Comment voulez-vous votre bureau ?",
                            "Vous pourrez changer à tout moment dans Paramètres › Bureau et Dock.")
        row = QHBoxLayout()
        row.addStretch()
        grp = QButtonGroup(self)
        for title, key, desc in (("Classique", "classique", "Une barre en bas, comme Windows."),
                                 ("Mac", "mac", "Barre de menus en haut, dock en bas.")):
            col = QVBoxLayout()
            c = ChoiceCard(title, lnf_preview(f"org.nounoursos.{key}"), w=320, h=180)
            c.setChecked(key == self.choice["layout"])
            c.clicked.connect(lambda _=False, k=key: self.choice.update(layout=k))
            grp.addButton(c)
            col.addWidget(c)
            col.addWidget(label(desc, "sub", align=Qt.AlignmentFlag.AlignCenter))
            row.addLayout(col)
            row.addSpacing(18)
        row.addStretch()
        lay.addLayout(row)
        lay.addStretch()
        return w

    def p_apps(self):
        w, lay = self._page("Applis recommandées",
                            "Une sélection NounoursCorp, installée en arrière-plan depuis Flathub. "
                            "Des milliers d'autres vous attendent dans Discover.")
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        for i, (app_id, name, desc, color, glyph) in enumerate(RECOMMENDED):
            card = Card()
            t = Toggle(False)
            t.toggled.connect(lambda on, a=app_id: (self.choice["apps"].add(a) if on
                                                    else self.choice["apps"].discard(a)))
            card.add(SettingRow(name, desc, t, tile_icon(None, color, 32, glyph)))
            grid.addWidget(card, i // 2, i % 2)
        lay.addLayout(grid)
        lay.addStretch()
        return w

    def p_updates(self):
        w, lay = self._page("Restez à jour",
                            "Les mises à jour apportent de nouvelles fonctions de NounoursOS "
                            "et protègent votre ordinateur.")
        card = Card()
        t1 = Toggle(True)
        t1.toggled.connect(lambda v: self.choice.update(auto_check=v))
        t2 = Toggle(True)
        t2.toggled.connect(lambda v: self.choice.update(auto_sec=v))
        card.add(SettingRow("Me prévenir des nouvelles versions de NounoursOS",
                            "Une notification apparaît quand une mise à jour est prête.", t1,
                            tile_icon("system-software-update", HONEY, 32, "↻")))
        card.add(SettingRow("Installer les correctifs de sécurité automatiquement",
                            "Recommandé. En arrière-plan, sans redémarrage forcé.", t2,
                            tile_icon("security-high", "#3FA36B", 32, "✓")))
        lay.addWidget(card)
        lay.addStretch()
        return w

    def p_done(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addStretch()
        lg = QLabel()
        lg.setPixmap(logo_pixmap(130))
        lay.addWidget(lg, 0, Qt.AlignmentFlag.AlignHCenter)
        self.done_title = label("Tout est prêt !", "title", align=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.done_title)
        lay.addWidget(label("Vos choix peuvent être modifiés à tout moment dans Paramètres.", "sub",
                            align=Qt.AlignmentFlag.AlignCenter))
        self.applying = label("", "sub", align=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.applying)
        lay.addStretch()
        return w

    # --- Application des choix -------------------------------------------------------
    def finish(self):
        self.next_b.setEnabled(False)
        self.applying.setText("Application de vos réglages…")
        QApplication.processEvents()
        ch = self.choice
        if not DEMO:
            # 1) disposition (réinitialise le thème global) puis 2) couleurs
            subprocess.run(["nounoursos-disposition", ch["layout"]])
            apply_color_scheme(ch["dark"], ch["accent"])
            if not ch["auto_sec"]:
                root_helper("auto-securite", "off")
        if ch["apps"] and not DEMO:
            spawn(["nounoursos-applis", *sorted(ch["apps"])])
        write_conf("apparence.conf", {"theme": "sombre" if ch["dark"] else "clair", "accent": ch["accent"]})
        write_conf("maj.conf", {"recherche_auto": "true" if ch["auto_check"] else "false"})
        os.makedirs(CONFIG_DIR, exist_ok=True)
        open(FLAG, "w").close()
        QTimer.singleShot(1200, self.close)


def install_desktop_icon():
    """En live : icône « Installer NounoursOS » sur le bureau."""
    src = "/usr/share/applications/nounoursos-installer.desktop"
    if not os.path.exists(src):
        return
    try:
        desk = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True).stdout.strip()
    except Exception:
        desk = ""
    desk = desk or os.path.expanduser("~/Desktop")
    os.makedirs(desk, exist_ok=True)
    dst = os.path.join(desk, "nounoursos-installer.desktop")
    with open(src) as f, open(dst, "w") as g:
        g.write(f.read())
    os.chmod(dst, 0o755)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    live = is_live() or "--live" in argv
    force = "--force" in argv
    if live and not DEMO:
        install_desktop_icon()
    if not force and os.path.exists(FLAG):
        return 0
    app = QApplication(sys.argv)
    app.setApplicationName("nounoursos-bienvenue")
    app.setDesktopFileName("nounoursos-bienvenue")
    app.setStyleSheet(stylesheet(LIGHT))
    w = LiveWelcome() if live else Assistant()
    if live:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        open(FLAG, "w").close()
    if "--windowed" in argv:
        w.resize(1280, 800)
        w.show()
    else:
        w.showFullScreen()
    return app.exec()
