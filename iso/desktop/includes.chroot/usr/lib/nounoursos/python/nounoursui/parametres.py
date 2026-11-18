"""Paramètres NounoursOS — réglages simplifiés, façon macOS.

Les réglages les plus utilisés sont gérés directement ici (Wi-Fi, Bluetooth,
Son, Apparence, Fond d'écran, Bureau et Dock, Mise à jour, À propos).
Les autres ouvrent seulement le module KDE concerné (kcmshell6), sans la
grosse fenêtre « Configuration du système ».
"""
import glob
import os
import re
import shutil
import socket
import sys

from PyQt6.QtCore import Qt, QSize, QRectF, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QListWidget, QListWidgetItem, QStackedWidget, QLineEdit, QLabel,
                             QScrollArea, QSlider, QGridLayout, QButtonGroup, QFrame,
                             QStyledItemDelegate, QStyle)

from . import (label, button, Card, SettingRow, Toggle, ChoiceCard, Swatch, tile_icon,
               logo_pixmap, colors, stylesheet, run, spawn, has, open_kcm, root_helper,
               user_info, os_release, read_conf, write_conf, apply_color_scheme, apply_accent,
               plasma_script, is_dark, ACCENTS, HONEY, LNF, WALLPAPERS, DEMO, CONFIG_DIR)
from . import updates as U

BLUE, RED, ORANGE, GREEN, PURPLE, GREY, PINK, TEAL = (
    "#3D7EDB", "#E5484D", "#E8833A", "#3FA36B", "#7E57C2", "#7C7586", "#D9568C", "#2BA3A3")

# clé, libellé, icône, couleur, lettre de secours, module KDE (None = page native),
# description, mots-clés pour la recherche
SECTIONS = [
    [("wifi", "Wi-Fi", "network-wireless", BLUE, "W", None, "", "internet sans fil reseau"),
     ("bluetooth", "Bluetooth", "preferences-system-bluetooth", BLUE, "B", None, "", "casque souris"),
     ("reseau", "Réseau", "network-wired", BLUE, "R", "kcm_networkmanagement",
      "Connexions filaires, VPN, partage de connexion et réglages avancés du réseau.", "vpn ethernet proxy")],
    [("notifications", "Notifications", "preferences-desktop-notification", RED, "N", "kcm_notifications",
      "Choisissez quelles applications peuvent vous envoyer des notifications, et le mode Ne pas déranger.",
      "ne pas deranger alertes"),
     ("son", "Son", "audio-volume-high", RED, "S", None, "", "volume haut-parleur micro audio")],
    [("maj", "Mise à jour", "system-software-update", GREY, "M", None, "", "mises a jour version securite"),
     ("apropos", "À propos", "help-about", GREY, "i", None, "", "version systeme info materiel"),
     ("apparence", "Apparence", "preferences-desktop-theme", "#3B2A4F", "A", None, "",
      "theme sombre clair couleur accent"),
     ("bureau", "Bureau et Dock", "preferences-desktop", "#3B2A4F", "D", None, "",
      "dock barre panneau disposition mac classique"),
     ("fond", "Fond d'écran", "preferences-desktop-wallpaper", TEAL, "F", None, "", "image wallpaper"),
     ("windows", "Applications Windows", "winboat", "#2F6FDB", "⊞", None, "",
      "winboat windows exe logiciels office photoshop"),
     ("ecrans", "Écrans", "preferences-desktop-display", BLUE, "É", "kcm_kscreen",
      "Résolution, mise à l'échelle, disposition de plusieurs écrans et éclairage nocturne.",
      "resolution moniteur luminosite nuit")],
    [("verrouillage", "Écran de verrouillage", "system-lock-screen", GREY, "V", "kcm_screenlocker",
      "Verrouillage automatique, délai avant mot de passe et apparence de l'écran de verrouillage.",
      "mot de passe veille"),
     ("utilisateurs", "Utilisateurs", "system-users", GREY, "U", "kcm_users",
      "Ajoutez ou modifiez des comptes, changez votre photo et votre mot de passe.", "compte mot de passe photo"),
     ("energie", "Énergie", "preferences-system-power-management", GREEN, "É", "kcm_powerdevilprofilesconfig",
      "Mise en veille, extinction de l'écran et comportement sur batterie.", "batterie veille")],
    [("langue", "Langue et région", "preferences-desktop-locale", BLUE, "L", "kcm_regionandlang",
      "Langue du système, formats de date, de nombres et de monnaie.", "francais format"),
     ("date", "Date et heure", "preferences-system-time", BLUE, "H", "kcm_clock",
      "Réglage de l'heure, fuseau horaire et synchronisation automatique.", "fuseau horloge"),
     ("clavier", "Clavier", "input-keyboard", GREY, "C", "kcm_keyboard",
      "Disposition du clavier (AZERTY…), répétition des touches et raccourcis.", "azerty raccourcis"),
     ("souris", "Souris et pavé tactile", "input-mouse", GREY, "S", "kcm_mouse",
      "Vitesse du pointeur, défilement et gestes du pavé tactile.", "touchpad trackpad pointeur"),
     ("imprimantes", "Imprimantes", "printer", GREY, "I", "kcm_printer_manager",
      "Ajouter une imprimante et gérer les impressions en cours.", "imprimer scanner"),
     ("applis", "Applications par défaut", "preferences-desktop-default-applications", GREY, "A",
      "kcm_componentchooser", "Navigateur, messagerie, lecteur de musique… utilisés par défaut.",
      "navigateur defaut"),
     ("demarrage", "Ouverture au démarrage", "system-run", GREY, "O", "kcm_autostart",
      "Applications lancées automatiquement à l'ouverture de session.", "autostart")],
]
ITEMS = {s[0]: s for group in SECTIONS for s in group}


# --------------------------------------------------------------------------
class SidebarDelegate(QStyledItemDelegate):
    """Dessine la pastille rouge (nombre de mises à jour) à droite de l'élément."""

    def paint(self, p, opt, idx):
        super().paint(p, opt, idx)
        n = idx.data(Qt.ItemDataRole.UserRole + 1)
        if n:
            p.save()
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            r = opt.rect
            d = 20
            rect = QRectF(r.right() - d - 12, r.center().y() - d / 2, d, d)
            p.setBrush(QColor("#E5484D"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(rect)
            p.setPen(QColor("white"))
            f = QFont("Noto Sans", 8)
            f.setBold(True)
            p.setFont(f)
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(n))
            p.restore()


def page(title, subtitle=None):
    """Page de réglages défilante, contenu centré (largeur max 660 px)."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    inner = QWidget()
    outer = QHBoxLayout(inner)
    outer.setContentsMargins(28, 22, 28, 28)
    col = QWidget()
    col.setMaximumWidth(660)
    lay = QVBoxLayout(col)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(12)
    lay.addWidget(label(title, "h1"))
    if subtitle:
        lay.addWidget(label(subtitle, "sub", wrap=True))
    outer.addWidget(col)
    scroll.setWidget(inner)
    scroll.body = lay
    return scroll


def finish(pg):
    pg.body.addStretch()
    return pg


def window_preview(dark, w=200, h=124):
    """Miniature d'un bureau clair ou sombre (choix du thème)."""
    pm = QPixmap(w * 2, h * 2)
    pm.setDevicePixelRatio(2)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.fillRect(0, 0, w, h, QColor("#2B2238" if dark else "#E9E1D8"))
    p.fillRect(QRectF(0, h - 18, w, 18), QColor("#1C1825" if dark else "#FFFFFF"))
    win = QColor("#2A2436" if dark else "#FFFFFF")
    bar = QColor("#3A3247" if dark else "#EFE9E3")
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(win)
    p.drawRoundedRect(QRectF(26, 16, w - 52, h - 46), 6, 6)
    p.setBrush(bar)
    p.drawRoundedRect(QRectF(26, 16, w - 52, 14), 6, 6)
    p.setBrush(QColor(HONEY))
    p.drawRoundedRect(QRectF(40, 44, 50, 9), 4, 4)
    p.setBrush(QColor("#4A4258" if dark else "#E6DED6"))
    for i in range(3):
        p.drawRoundedRect(QRectF(40, 60 + i * 11, w - 90 - i * 20, 6), 3, 3)
    p.end()
    return pm


def lnf_preview(lnf_id):
    path = os.path.join(LNF, lnf_id, "contents", "previews", "preview.png")
    return QPixmap(path) if os.path.exists(path) else QPixmap()


# ==========================================================================
class Settings(QMainWindow):
    def __init__(self, start=None):
        super().__init__()
        self.setWindowTitle("Paramètres")
        self.setWindowIcon(QIcon.fromTheme("preferences-system"))
        self.resize(1000, 680)
        self.pages = {}

        central = QWidget()
        central.setObjectName("Page")
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # --- Barre latérale ---
        side = QFrame()
        side.setObjectName("Sidebar")
        side.setFixedWidth(260)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(10, 14, 10, 10)
        sv.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.filter)
        sv.addWidget(self.search)
        sv.addWidget(self.user_card())
        self.list = QListWidget()
        self.list.setIconSize(QSize(24, 24))
        self.list.setItemDelegate(SidebarDelegate(self.list))
        self.list.currentItemChanged.connect(self.on_select)
        sv.addWidget(self.list, 1)
        adv = button("Réglages avancés…", "link", lambda: spawn(["systemsettings"]))
        sv.addWidget(adv, 0, Qt.AlignmentFlag.AlignLeft)
        h.addWidget(side)

        self.stack = QStackedWidget()
        h.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.fill_list()
        self.select(start or "maj" if U.load_state().count else (start or "wifi"))
        # Rafraîchir la pastille de mise à jour de temps en temps
        self.badge_timer = QTimer(self)
        self.badge_timer.timeout.connect(self.refresh_badge)
        self.badge_timer.start(60_000)

    # --- Barre latérale ------------------------------------------------------
    def user_card(self):
        login, full = user_info()
        w = QFrame()
        w.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 6, 6, 6)
        av = QLabel()
        face = os.path.expanduser("~/.face.icon")
        if os.path.exists(face):
            pm = QPixmap(face).scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                      Qt.TransformationMode.SmoothTransformation)
        else:
            pm = tile_icon(None, HONEY, 44, (full or login)[:1].upper())
        av.setPixmap(pm)
        lay.addWidget(av)
        v = QVBoxLayout()
        v.setSpacing(0)
        n = label(full)
        n.setStyleSheet("font-weight: 700; font-size: 10.5pt;")
        v.addWidget(n)
        v.addWidget(label("Compte NounoursOS", "sub"))
        lay.addLayout(v, 1)
        w.mouseReleaseEvent = lambda e: open_kcm("kcm_users")
        return w

    def fill_list(self):
        self.list.clear()
        count = U.load_state().count
        for gi, group in enumerate(SECTIONS):
            if gi:
                sep = QListWidgetItem()
                sep.setFlags(Qt.ItemFlag.NoItemFlags)
                sep.setSizeHint(QSize(10, 10))
                sep.setData(Qt.ItemDataRole.UserRole, None)
                self.list.addItem(sep)
            for key, title, icon, color, glyph, kcm, desc, kw in group:
                it = QListWidgetItem(QIcon(tile_icon(icon, color, 24, glyph)), title)
                it.setData(Qt.ItemDataRole.UserRole, key)
                it.setSizeHint(QSize(200, 34))
                if key == "maj" and count:
                    it.setData(Qt.ItemDataRole.UserRole + 1, count)
                self.list.addItem(it)

    def refresh_badge(self):
        count = U.load_state().count
        for i in range(self.list.count()):
            it = self.list.item(i)
            if it.data(Qt.ItemDataRole.UserRole) == "maj":
                it.setData(Qt.ItemDataRole.UserRole + 1, count or None)

    def filter(self, text):
        t = text.strip().lower()
        t_norm = _strip_accents(t)
        for i in range(self.list.count()):
            it = self.list.item(i)
            key = it.data(Qt.ItemDataRole.UserRole)
            if key is None:
                it.setHidden(bool(t))
                continue
            entry = ITEMS[key]
            hay = _strip_accents((entry[1] + " " + entry[7] + " " + entry[6]).lower())
            it.setHidden(bool(t) and t_norm not in hay)

    def select(self, key):
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.ItemDataRole.UserRole) == key:
                self.list.setCurrentRow(i)
                return

    def on_select(self, cur, _prev):
        if not cur:
            return
        key = cur.data(Qt.ItemDataRole.UserRole)
        if key is None:
            return
        if key not in self.pages:
            self.pages[key] = self.build(key)
            self.stack.addWidget(self.pages[key])
        self.stack.setCurrentWidget(self.pages[key])

    # --- Pages ------------------------------------------------------------------
    def build(self, key):
        builder = getattr(self, "page_" + key, None)
        if builder:
            return builder()
        return self.page_kcm(key)

    def page_kcm(self, key):
        _, title, icon, color, glyph, kcm, desc, _kw = ITEMS[key]
        pg = page(title)
        card = Card(margins=(20, 20, 20, 20))
        row = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(tile_icon(icon, color, 56, glyph))
        row.addWidget(ic, 0, Qt.AlignmentFlag.AlignTop)
        v = QVBoxLayout()
        v.addWidget(label(desc, wrap=True))
        b = button(f"Ouvrir les réglages « {title} »", "primary", lambda: open_kcm(kcm))
        v.addWidget(b, 0, Qt.AlignmentFlag.AlignLeft)
        row.addLayout(v, 1)
        w = QWidget()
        w.setLayout(row)
        card.add(w)
        pg.body.addWidget(card)
        if key == "souris":
            pg.body.addWidget(button("Réglages du pavé tactile…", None, lambda: open_kcm("kcm_touchpad")),
                              0, Qt.AlignmentFlag.AlignLeft)
        return finish(pg)

    # Wi-Fi ---------------------------------------------------------------------
    def page_wifi(self):
        pg = page("Wi-Fi")
        on = DEMO or "enabled" in run("nmcli radio wifi")
        tog = Toggle(on)
        tog.toggled.connect(lambda v: spawn(["nmcli", "radio", "wifi", "on" if v else "off"]))
        card = Card()
        card.add(SettingRow("Wi-Fi", None, tog, tile_icon("network-wireless", BLUE, 30, "W")))
        cur = self._current_wifi()
        card.add(SettingRow(cur or "Non connecté", "Réseau actuel" if cur else
                            "Choisissez un réseau ci-dessous", None))
        pg.body.addWidget(card)

        pg.body.addWidget(label("RÉSEAUX DISPONIBLES", "section"))
        nets = Card()
        found = self._wifi_list()
        if not found:
            nets.add(SettingRow("Aucun réseau détecté", "Le Wi-Fi est peut-être désactivé.", None))
        for ssid, signal, secure in found[:8]:
            bars = "▂▄▆█"[: max(1, min(4, int(signal) // 25 + 1))]
            r = SettingRow(ssid, ("🔒 Sécurisé · " if secure else "Ouvert · ") + f"signal {signal} %",
                           label(bars, "sub"), chevron=True)
            r.clicked.connect(lambda: open_kcm("kcm_networkmanagement"))
            nets.add(r)
        pg.body.addWidget(nets)
        pg.body.addWidget(label("Pour vous connecter à un réseau protégé, cliquez dessus ou utilisez "
                                "l'icône réseau dans la barre.", "sub", wrap=True))
        pg.body.addWidget(button("Réglages réseau avancés…", None,
                                 lambda: open_kcm("kcm_networkmanagement")), 0, Qt.AlignmentFlag.AlignLeft)
        return finish(pg)

    def _current_wifi(self):
        if DEMO:
            return "Freebox-NounoursCorp"
        for line in run("nmcli -t -f ACTIVE,SSID dev wifi").splitlines():
            if line.startswith("yes:") or line.startswith("oui:"):
                return line.split(":", 1)[1]
        return ""

    def _wifi_list(self):
        if DEMO:
            return [("Freebox-NounoursCorp", "92", True), ("Livebox-4F2A", "64", True),
                    ("Wi-Fi Invités", "41", False)]
        seen, out = set(), []
        for line in run("nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list").splitlines():
            parts = re.split(r"(?<!\\):", line)
            if len(parts) >= 3 and parts[0] and parts[0] not in seen:
                seen.add(parts[0])
                out.append((parts[0].replace("\\:", ":"), parts[1] or "0", parts[2] not in ("", "--")))
        return out

    # Bluetooth ----------------------------------------------------------------
    def page_bluetooth(self):
        pg = page("Bluetooth")
        on = DEMO or "Powered: yes" in run("bluetoothctl show")
        tog = Toggle(on)
        tog.toggled.connect(lambda v: spawn(["bluetoothctl", "power", "on" if v else "off"]))
        card = Card()
        card.add(SettingRow("Bluetooth", "Visible sous le nom « " + socket.gethostname() + " »", tog,
                            tile_icon("preferences-system-bluetooth", BLUE, 30, "B")))
        pg.body.addWidget(card)
        pg.body.addWidget(label("MES APPAREILS", "section"))
        devs = Card()
        lst = [("Casque Nounours", "Connecté")] if DEMO else [
            (l.split(" ", 2)[2], "Associé") for l in run("bluetoothctl devices Paired").splitlines()
            if l.startswith("Device ") and len(l.split(" ", 2)) == 3]
        if not lst:
            devs.add(SettingRow("Aucun appareil", "Ajoutez un casque, une souris, un clavier…", None))
        for name, st in lst:
            devs.add(SettingRow(name, st, None))
        pg.body.addWidget(devs)
        pg.body.addWidget(button("Ajouter un appareil…", "primary", lambda: spawn(["bluedevil-wizard"])),
                          0, Qt.AlignmentFlag.AlignLeft)
        return finish(pg)

    # Son ------------------------------------------------------------------------
    def page_son(self):
        pg = page("Son")
        vol, muted = self._volume()
        card = Card()
        sl = QSlider(Qt.Orientation.Horizontal)
        sl.setRange(0, 100)
        sl.setValue(vol)
        sl.setFixedWidth(260)
        sl.valueChanged.connect(lambda v: spawn(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{v}%"]))
        card.add(SettingRow("Volume de sortie", None, sl, tile_icon("audio-volume-high", RED, 30, "♪")))
        mute = Toggle(muted)
        mute.toggled.connect(lambda v: spawn(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1" if v else "0"]))
        card.add(SettingRow("Couper le son", None, mute))
        card.add(SettingRow("Sortie", self._sink_name(), None))
        pg.body.addWidget(card)
        pg.body.addWidget(button("Choisir la sortie et l'entrée (micro)…", None,
                                 lambda: open_kcm("kcm_pulseaudio")), 0, Qt.AlignmentFlag.AlignLeft)
        return finish(pg)

    def _volume(self):
        if DEMO:
            return 65, False
        out = run("wpctl get-volume @DEFAULT_AUDIO_SINK@")
        m = re.search(r"Volume:\s*([\d.]+)", out)
        return (int(float(m.group(1)) * 100) if m else 50), "MUTED" in out

    def _sink_name(self):
        if DEMO:
            return "Haut-parleurs intégrés"
        m = re.search(r'node\.description = "([^"]+)"', run("wpctl inspect @DEFAULT_AUDIO_SINK@"))
        return m.group(1) if m else "Sortie audio par défaut"

    # Apparence ------------------------------------------------------------------
    def page_apparence(self):
        pg = page("Apparence")
        pg.body.addWidget(label("THÈME", "section"))
        card = Card(margins=(16, 16, 16, 12))
        row = QHBoxLayout()
        grp = QButtonGroup(self)
        dark = is_dark()
        for title, d in (("Clair", False), ("Sombre", True)):
            c = ChoiceCard(title, window_preview(d), w=200, h=124)
            c.setChecked(d == dark)
            c.clicked.connect(lambda _=False, d=d: self._set_theme(d))
            grp.addButton(c)
            row.addWidget(c)
        row.addStretch()
        w = QWidget()
        w.setLayout(row)
        card.add(w)
        pg.body.addWidget(card)

        pg.body.addWidget(label("COULEUR D'ACCENTUATION", "section"))
        acc = Card(margins=(16, 12, 16, 12))
        r2 = QHBoxLayout()
        cur = read_conf("apparence.conf", {"accent": HONEY}).get("accent")
        for name, col in ACCENTS:
            s = Swatch(col, name)
            s.setChecked(col.lower() == cur.lower())
            s.clicked.connect(lambda _=False, col=col: self._set_accent(col))
            r2.addWidget(s)
        r2.addStretch()
        w2 = QWidget()
        w2.setLayout(r2)
        acc.add(w2)
        pg.body.addWidget(acc)

        more = Card()
        for t, k in (("Polices", "kcm_fonts"), ("Icônes", "kcm_icons"), ("Pointeur de la souris", "kcm_cursortheme")):
            r = SettingRow(t, None, chevron=True)
            r.clicked.connect(lambda k=k: open_kcm(k))
            more.add(r)
        pg.body.addWidget(more)
        return finish(pg)

    def _set_theme(self, dark):
        accent = read_conf("apparence.conf", {"accent": HONEY}).get("accent")
        apply_color_scheme(dark, accent)
        write_conf("apparence.conf", {"theme": "sombre" if dark else "clair"})

    def _set_accent(self, col):
        apply_accent(col)
        write_conf("apparence.conf", {"accent": col})

    # Fond d'écran ---------------------------------------------------------------
    def page_fond(self):
        pg = page("Fond d'écran")
        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setSpacing(14)
        grp = QButtonGroup(self)
        for i, (name, target, thumb) in enumerate(self._wallpapers()):
            c = ChoiceCard(name, QPixmap(thumb), w=196, h=112)
            c.clicked.connect(lambda _=False, t=target: spawn(["plasma-apply-wallpaperimage", t]))
            grp.addButton(c)
            grid.addWidget(c, i // 3, i % 3)
        pg.body.addWidget(grid_w)
        pg.body.addWidget(button("Ajouter une photo…", None, self._pick_wallpaper), 0, Qt.AlignmentFlag.AlignLeft)
        return finish(pg)

    def _wallpapers(self):
        out = []
        for d in sorted(glob.glob(os.path.join(WALLPAPERS, "*"))):
            if os.path.isdir(d):
                imgs = sorted(glob.glob(os.path.join(d, "contents", "images", "*")))
                shot = os.path.join(d, "contents", "screenshot.png")
                thumb = shot if os.path.exists(shot) else (imgs[0] if imgs else None)
                if thumb:
                    out.append((os.path.basename(d), d, thumb))
            elif d.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                out.append((os.path.splitext(os.path.basename(d))[0], d, d))
        out.sort(key=lambda x: x[0] != "NounoursOS")
        return out[:24]

    def _pick_wallpaper(self):
        from PyQt6.QtWidgets import QFileDialog
        f, _ = QFileDialog.getOpenFileName(self, "Choisir une image", os.path.expanduser("~/Images"),
                                           "Images (*.png *.jpg *.jpeg *.webp)")
        if f:
            spawn(["plasma-apply-wallpaperimage", f])

    # Bureau et Dock -------------------------------------------------------------
    def page_bureau(self):
        pg = page("Bureau et Dock")
        pg.body.addWidget(label("DISPOSITION", "section"))
        card = Card(margins=(16, 16, 16, 12))
        row = QHBoxLayout()
        grp = QButtonGroup(self)
        cur = "classique"
        try:
            with open(os.path.join(CONFIG_DIR, "disposition")) as f:
                cur = f.read().strip() or "classique"
        except OSError:
            pass
        for title, key in (("Classique", "classique"), ("Mac", "mac")):
            c = ChoiceCard(title, lnf_preview(f"org.nounoursos.{key}"), w=240, h=135)
            c.setChecked(key == cur)
            c.clicked.connect(lambda _=False, k=key: spawn(["nounoursos-disposition", k]))
            grp.addButton(c)
            row.addWidget(c)
        row.addStretch()
        w = QWidget()
        w.setLayout(row)
        card.add(w)
        pg.body.addWidget(card)
        pg.body.addWidget(label("Changer de disposition réinitialise la barre et le dock.", "sub"))

        pg.body.addWidget(label("DOCK ET BARRE DES TÂCHES", "section"))
        opts = Card()
        hide = Toggle(False)
        hide.toggled.connect(lambda v: plasma_script(
            "panels().forEach(function(p){ if (p.location == 'bottom') p.hiding = '%s'; })"
            % ("autohide" if v else "dodgewindows")))
        opts.add(SettingRow("Masquer automatiquement", "Le dock apparaît quand la souris touche le bas de l'écran.",
                            hide))
        size = QSlider(Qt.Orientation.Horizontal)
        size.setRange(32, 96)
        size.setValue(56)
        size.setFixedWidth(220)
        size.sliderReleased.connect(lambda: plasma_script(
            "panels().forEach(function(p){ if (p.location == 'bottom') p.height = %d; })" % size.value()))
        opts.add(SettingRow("Taille", None, size))
        pg.body.addWidget(opts)
        return finish(pg)

    # Mise à jour ------------------------------------------------------------------
    def page_maj(self):
        pg = page("Mise à jour")
        self.maj_card = Card(margins=(20, 18, 20, 18))
        box = QWidget()
        h = QHBoxLayout(box)
        h.setContentsMargins(0, 0, 0, 0)
        logo = QLabel()
        logo.setPixmap(logo_pixmap(72))
        h.addWidget(logo, 0, Qt.AlignmentFlag.AlignTop)
        v = QVBoxLayout()
        self.maj_title = label("", "h2")
        self.maj_title.setStyleSheet("font-size: 13pt; font-weight: 700;")
        self.maj_sub = label("", "sub", wrap=True)
        v.addWidget(self.maj_title)
        v.addWidget(self.maj_sub)
        btns = QHBoxLayout()
        self.maj_btn = button("", "primary", lambda: spawn(["nounoursos-maj"]))
        btns.addWidget(self.maj_btn)
        btns.addStretch()
        v.addLayout(btns)
        h.addLayout(v, 1)
        self.maj_card.add(box)
        pg.body.addWidget(self.maj_card)
        self._maj_refresh()

        pg.body.addWidget(label("RÉGLAGES", "section"))
        conf = read_conf("maj.conf", {"recherche_auto": "true"})
        auto = Toggle(conf.get("recherche_auto") == "true")
        auto.toggled.connect(lambda v: write_conf("maj.conf", {"recherche_auto": "true" if v else "false"}))
        sec = Toggle(_auto_security_enabled())
        def set_sec(v):
            if not root_helper("auto-securite", "on" if v else "off"):
                sec.blockSignals(True)       # mot de passe refusé : on remet l'interrupteur
                sec.setChecked(not v)
                sec.blockSignals(False)
        sec.toggled.connect(set_sec)
        opts = Card()
        opts.add(SettingRow("Rechercher automatiquement",
                            "Vous êtes prévenu dès qu'une mise à jour de NounoursOS est disponible.", auto))
        opts.add(SettingRow("Installer les correctifs de sécurité automatiquement",
                            "Recommandé. Installés en arrière-plan, sans redémarrage forcé.", sec))
        pg.body.addWidget(opts)
        return finish(pg)

    def _maj_refresh(self):
        s = U.load_state()
        rel = os_release()
        if s.count:
            self.maj_title.setText(s.headline() + (" est disponible" if s.new_release else ""))
            self.maj_sub.setText(s.summary())
            self.maj_btn.setText("Mettre à jour…")
        else:
            self.maj_title.setText("NounoursOS est à jour")
            self.maj_sub.setText(f"NounoursOS {rel.get('VERSION_ID', '')} « {rel.get('NOUNOURSOS_CODENAME', '')} »")
            self.maj_btn.setText("Rechercher des mises à jour")

    # Applications Windows (WinBoat) ---------------------------------------------------
    def page_windows(self):
        pg = page("Applications Windows",
                  "WinBoat fait tourner un vrai Windows en arrière-plan et affiche ses logiciels "
                  "dans des fenêtres NounoursOS, comme des applications normales.")
        checks = self._winboat_checks()
        card = Card()
        for title, ok, detail in checks:
            mark = label("✅" if ok else "⚠️")
            mark.setStyleSheet("font-size: 13pt;")
            card.add(SettingRow(title, detail, mark))
        pg.body.addWidget(label("VÉRIFICATIONS", "section"))
        pg.body.addWidget(card)

        row = QHBoxLayout()
        in_group = next((ok for t, ok, _ in checks if t == "Accès à Docker"), True)
        if not in_group:
            fix = button("Autoriser WinBoat…", None, None)

            def do_fix():
                if root_helper("groupe-docker"):
                    fix.setEnabled(False)
                    fix.setText("Fait : déconnectez-vous puis reconnectez-vous")
            fix.clicked.connect(do_fix)
            row.addWidget(fix)
        launch = button("Ouvrir WinBoat", "primary", lambda: spawn([self._winboat_bin()]))
        launch.setEnabled(bool(self._winboat_bin()))
        row.addWidget(launch)
        row.addStretch()
        w = QWidget()
        w.setLayout(row)
        pg.body.addWidget(w)
        pg.body.addWidget(label("Au premier lancement, WinBoat télécharge et installe Windows "
                                "(environ 30 minutes). Prévoyez au moins 32 Go libres.",
                                "sub", wrap=True))
        return finish(pg)

    def _winboat_bin(self):
        if DEMO:
            return "winboat"
        for c in ("winboat", "/opt/WinBoat/winboat", "/opt/winboat/winboat"):
            if shutil.which(c) or os.path.exists(c):
                return c
        return ""

    def _winboat_checks(self):
        if DEMO:
            return [("WinBoat", True, "Installé"), ("Virtualisation (KVM)", True, "Activée"),
                    ("Mémoire", True, "16 Go (4 Go minimum)"), ("Espace libre", True, "87 Go (32 Go minimum)"),
                    ("Docker", True, "Installé"), ("Accès à Docker", False, "Votre compte doit être autorisé"),
                    ("FreeRDP 3", True, "Installé")]
        import grp
        try:
            with open("/proc/meminfo") as f:
                mem = int(f.readline().split()[1]) / 1024 / 1024
        except Exception:
            mem = 0
        free = shutil.disk_usage(os.path.expanduser("~")).free / 1024 ** 3
        try:
            names = {grp.getgrgid(g).gr_name for g in os.getgroups()}
            in_docker = "docker" in names
        except Exception:
            in_docker = False
        return [
            ("WinBoat", bool(self._winboat_bin()), "Installé" if self._winboat_bin() else "Non installé"),
            ("Virtualisation (KVM)", os.path.exists("/dev/kvm"),
             "Activée" if os.path.exists("/dev/kvm") else "À activer dans le BIOS/UEFI (VT-x / AMD-V)"),
            ("Mémoire", mem >= 3.6, f"{mem:.0f} Go (4 Go minimum)"),
            ("Espace libre", free >= 32, f"{free:.0f} Go (32 Go minimum)"),
            ("Docker", has("docker"), "Installé" if has("docker") else "Non installé"),
            ("Accès à Docker", in_docker,
             "Autorisé" if in_docker else "Votre compte doit être autorisé"),
            ("FreeRDP 3", has("xfreerdp3"), "Installé" if has("xfreerdp3") else "Non installé"),
        ]

    # À propos ---------------------------------------------------------------------
    def page_apropos(self):
        pg = page("À propos")
        rel = os_release()
        top = QVBoxLayout()
        top.setSpacing(4)
        lg = QLabel()
        lg.setPixmap(logo_pixmap(120))
        top.addWidget(lg, 0, Qt.AlignmentFlag.AlignHCenter)
        t = label("NounoursOS", "title", align=Qt.AlignmentFlag.AlignCenter)
        top.addWidget(t)
        top.addWidget(label(f"Version {rel.get('VERSION_ID', '')} « {rel.get('NOUNOURSOS_CODENAME', '')} »",
                            "sub", align=Qt.AlignmentFlag.AlignCenter))
        w = QWidget()
        w.setLayout(top)
        pg.body.addWidget(w)
        info = Card()
        for k, v in self._hardware():
            info.add(SettingRow(k, None, label(v, "sub")))
        pg.body.addWidget(info)
        row = QHBoxLayout()
        row.addWidget(button("Rapport système…", None, lambda: spawn(["kinfocenter"])))
        row.addWidget(button("nounourscorp.fr", "link", lambda: spawn(["xdg-open", "https://nounourscorp.fr"])))
        row.addStretch()
        rw = QWidget()
        rw.setLayout(row)
        pg.body.addWidget(rw)
        pg.body.addWidget(label("NounoursOS est basé sur Debian GNU/Linux. © NounoursCorp.", "sub",
                                align=Qt.AlignmentFlag.AlignCenter))
        return finish(pg)

    def _hardware(self):
        if DEMO:
            return [("Nom", "nounoursos"), ("Processeur", "AMD Ryzen 5 5600X (12 cœurs)"),
                    ("Mémoire", "16 Go"), ("Graphisme", "AMD Radeon RX 6600"),
                    ("Stockage", "38 Go disponibles sur 128 Go"), ("Bureau", "KDE Plasma 6")]
        cpu, cores = "Inconnu", 0
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name") and cpu == "Inconnu":
                        cpu = re.sub(r"\s+", " ", line.split(":", 1)[1].strip())
                    if line.startswith("processor"):
                        cores += 1
        except OSError:
            pass
        mem = "?"
        try:
            with open("/proc/meminfo") as f:
                kb = int(f.readline().split()[1])
                mem = f"{round(kb / 1024 / 1024)} Go"
        except Exception:
            pass
        gpu = "Inconnu"
        for line in run("lspci").splitlines():
            if "VGA" in line or "3D controller" in line or "Display controller" in line:
                gpu = line.split(": ", 1)[-1]
                gpu = re.sub(r"\s*\(rev .*\)$", "", gpu)
                break
        du = shutil.disk_usage("/")
        disk = f"{du.free // 1024 ** 3} Go disponibles sur {du.total // 1024 ** 3} Go"
        plasma = run("plasmashell --version").strip().replace("plasmashell", "KDE Plasma") or "KDE Plasma"
        return [("Nom", socket.gethostname()), ("Processeur", f"{cpu} ({cores} cœurs)"),
                ("Mémoire", mem), ("Graphisme", gpu), ("Stockage", disk), ("Bureau", plasma)]


def _auto_security_enabled():
    if DEMO:
        return True
    try:
        with open("/etc/apt/apt.conf.d/20auto-upgrades") as f:
            return 'Unattended-Upgrade "1"' in f.read()
    except OSError:
        return False


def _strip_accents(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    app = QApplication(sys.argv)
    app.setApplicationName("nounoursos-parametres")
    app.setApplicationDisplayName("Paramètres")
    app.setDesktopFileName("nounoursos-parametres")
    app.setStyleSheet(stylesheet())
    start = argv[0] if argv and argv[0] in ITEMS else None
    w = Settings(start)
    w.show()
    return app.exec()
