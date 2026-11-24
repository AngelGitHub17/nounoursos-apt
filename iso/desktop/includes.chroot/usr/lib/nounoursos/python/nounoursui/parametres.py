"""Paramètres NounoursOS — TOUS les réglages au même endroit, façon macOS.

- Pages NounoursOS : Wi-Fi, Bluetooth, Son, Apparence, Fond d'écran, Bureau et
  Dock, Mise à jour, À propos, Applications Windows.
- Tous les autres réglages sont les modules KDE eux-mêmes, affichés DANS la
  fenêtre (via libnounoursos-kcm.so), avec Appliquer / Rétablir / Par défaut.
- « Tous les réglages » liste chaque module installé : rien n'oblige à sortir.
"""
import glob
import os
import re
import shutil
import socket
import sys

from PyQt6.QtCore import Qt, QSize, QRectF, QTimer, QFileSystemWatcher
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QListWidget, QListWidgetItem, QStackedWidget, QLineEdit, QLabel,
                             QScrollArea, QSlider, QGridLayout, QButtonGroup, QFrame,
                             QStyledItemDelegate, QStyle, QMessageBox)

from . import (label, button, Card, SettingRow, Toggle, ChoiceCard, Swatch, tile_icon,
               logo_pixmap, colors, stylesheet, run, spawn, has, open_kcm, root_helper,
               user_info, os_release, read_conf, write_conf, apply_color_scheme, apply_accent, fond_anime, teinte_de,
               plasma_script, plasma_query, is_dark, ACCENTS, HONEY, LNF, WALLPAPERS, DEMO, CONFIG_DIR, DATA)
from . import updates as U
from . import kcm as K
from .maj import CheckThread

BLUE, RED, ORANGE, GREEN, PURPLE, GREY, PINK, TEAL = (
    "#3D7EDB", "#E5484D", "#E8833A", "#3FA36B", "#7E57C2", "#7C7586", "#D9568C", "#2BA3A3")

# clé, libellé, icônes (thème, candidats séparés par |), couleur et lettre de secours,
# module KDE (None = page NounoursOS), description, mots-clés pour la recherche
SECTIONS = [
    [("wifi", "Wi-Fi", "network-wireless-connected-100|network-wireless|preferences-system-network", BLUE, "W", None, "",
      "internet sans fil reseau"),
     ("bluetooth", "Bluetooth", "preferences-system-bluetooth|bluetooth|preferences-system-network", BLUE, "B", None, "", "casque souris"),
     ("reseau", "Réseau", "preferences-system-network", BLUE, "R", "kcm_networkmanagement",
      "", "vpn ethernet proxy filaire")],
    [("notifications", "Notifications", "preferences-desktop-notification-bell", RED, "N",
      "kcm_notifications", "", "ne pas deranger alertes"),
     ("son", "Son", "preferences-desktop-sound", RED, "S", None, "", "volume haut-parleur micro audio")],
    [("maj", "Mise à jour", "system-software-update", GREY, "M", None, "", "mises a jour version securite"),
     ("apropos", "À propos", "hwinfo|computer|help-about", GREY, "i", None, "",
      "version systeme info materiel"),
     ("windows", "Applications Windows", "winboat|computer", "#2F6FDB", "⊞", None, "",
      "winboat windows exe logiciels office photoshop")],
    [("apparence", "Apparence", "preferences-desktop-theme-global", "#3B2A4F", "A", None, "",
      "theme sombre clair couleur accent"),
     ("bureau", "Bureau et Dock", "preferences-desktop", "#3B2A4F", "D", None, "",
      "dock barre panneau disposition mac classique"),
     ("fond", "Fond d'écran", "preferences-desktop-wallpaper", TEAL, "F", None, "", "image wallpaper"),
     ("ecrans", "Écrans", "preferences-desktop-display-randr|preferences-desktop-display", BLUE, "É",
      "kcm_kscreen", "", "resolution moniteur luminosite nuit echelle"),
     ("polices", "Polices", "preferences-desktop-font", GREY, "P", "kcm_fonts", "", "texte taille"),
     ("couleurs", "Couleurs", "preferences-desktop-color", GREY, "C", "kcm_colors", "", "schema"),
     ("icones", "Icônes", "preferences-desktop-icons", GREY, "I", "kcm_icons", "", "theme icones"),
     ("pointeur", "Pointeur", "preferences-desktop-cursors", GREY, "P", "kcm_cursortheme", "",
      "curseur souris"),
     ("effets", "Effets", "preferences-desktop-effects", PURPLE, "E", "kcm_kwin_effects", "",
      "animation transparence flou"),
     ("splash", "Écran de chargement", "preferences-system-splash", PURPLE, "C", "kcm_splashscreen", "",
      "demarrage session")],
    [("fenetres", "Fenêtres", "preferences-system-windows-behavior|preferences-system-windows", GREY, "F",
      "kcm_kwinoptions", "", "focus clic barre titre"),
     ("bureaux", "Bureaux virtuels", "preferences-desktop-virtual", GREY, "B", "kcm_kwin_virtualdesktops",
      "", "espaces"),
     ("raccourcis", "Raccourcis clavier", "preferences-desktop-keyboard-shortcut", GREY, "R", "kcm_keys",
      "", "touches combinaison"),
     ("recherche", "Recherche", "system-search", GREY, "R", "kcm_plasmasearch", "", "krunner spotlight")],
    [("veille", "Écran de veille", "preferences-desktop-screensaver", "#5B5BD6", "V", None, "",
      "economiseur screensaver horloge inactivite"),
     ("verrouillage", "Écran de verrouillage", "system-lock-screen", GREY, "V", "kcm_screenlocker", "",
      "mot de passe veille"),
     ("empreinte", "Empreinte et visage", "preferences-desktop-user-password", PINK, "E", None, "",
      "empreinte digitale doigt touch id visage howdy deverrouillage"),
     ("utilisateurs", "Utilisateurs", "preferences-system-users|system-users", GREY, "U", "kcm_users", "",
      "compte mot de passe photo"),
     ("connexion", "Écran de connexion", "preferences-system-login", GREY, "C", "kcm_sddm", "",
      "sddm ouverture session"),
     ("energie", "Énergie", "preferences-system-power-management", GREEN, "É",
      "kcm_powerdevilprofilesconfig", "", "batterie veille"),
     ("accessibilite", "Accessibilité", "preferences-desktop-accessibility", BLUE, "A", "kcm_access", "",
      "malvoyant loupe")],
    [("langue", "Langue et région", "preferences-desktop-locale", BLUE, "L", "kcm_regionandlang", "",
      "francais format"),
     ("date", "Date et heure", "preferences-system-time", BLUE, "H", "kcm_clock", "", "fuseau horloge"),
     ("clavier", "Clavier", "preferences-desktop-keyboard|input-keyboard", GREY, "C", "kcm_keyboard", "",
      "azerty disposition"),
     ("souris", "Souris", "preferences-desktop-mouse|input-mouse", GREY, "S", "kcm_mouse", "",
      "pointeur vitesse"),
     ("pave", "Pavé tactile", "preferences-desktop-touchpad|input-touchpad", GREY, "P", "kcm_touchpad", "",
      "touchpad trackpad gestes"),
     ("imprimantes", "Imprimantes", "printer", GREY, "I", "kcm_printer_manager", "", "imprimer scanner"),
     ("applis", "Applications par défaut", "preferences-desktop-default-applications", GREY, "A",
      "kcm_componentchooser", "", "navigateur defaut"),
     ("fichiers", "Associations de fichiers", "preferences-desktop-filetype-association", GREY, "F",
      "kcm_filetypes", "", "ouvrir avec type"),
     ("demarrage", "Ouverture au démarrage", "preferences-system-session-services|system-run", GREY, "O",
      "kcm_autostart", "", "autostart"),
     ("session", "Session", "preferences-system-session-services", GREY, "S", "kcm_smserver", "",
      "eteindre redemarrer"),
     ("disques", "Disques et clés USB", "preferences-system-disks|drive-harddisk", GREY, "D",
      "kcm_device_automounter", "", "montage usb")],
    [("tous", "Tous les réglages", "applications-system|preferences-system", GREY, "…", None, "",
      "avance avances kde configuration")],
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


ICONES = DATA + "/icones"


def nounours_icon(key, size):
    """Icône NounoursOS dessinée pour Paramètres (usr/share/nounoursos/icones)."""
    path = os.path.join(ICONES, key + ".svg")
    if key and os.path.exists(path):
        return QIcon(path).pixmap(QSize(size, size))
    return None


def real_icon(names, size, color=GREY, glyph="•", key=None):
    """Icône NounoursOS si elle existe, sinon icône du thème, sinon pastille de secours."""
    pm = nounours_icon(key, size) if key else None
    if pm is not None and not pm.isNull():
        return pm
    for n in (names or "").split("|"):
        if n and QIcon.hasThemeIcon(n):
            return QIcon.fromTheme(n).pixmap(QSize(size, size))
    return tile_icon(None, color, size, glyph)


def page(title, subtitle=None):
    """Page de réglages défilante, contenu centré (largeur max 660 px)."""
    scroll = QScrollArea()
    scroll.setObjectName("NPage")
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
CATEGORIES = {
    "appearance": "Apparence", "appearanceandstyle": "Apparence", "colors": "Apparence",
    "fonts": "Apparence", "icons": "Apparence", "themes": "Apparence", "decorations": "Apparence",
    "workspace": "Espace de travail", "workspacetheme": "Espace de travail", "desktopbehavior": "Espace de travail",
    "windowmanagement": "Fenêtres", "shortcuts": "Raccourcis", "search": "Recherche",
    "personalization": "Personnalisation", "applications": "Applications",
    "applications-defaults": "Applications", "notifications": "Notifications",
    "regionalsettings": "Langue et région", "accessibility": "Accessibilité",
    "network": "Réseau", "connectivity": "Réseau", "networksettings": "Réseau", "bluetooth": "Réseau",
    "hardware": "Matériel", "input-devices": "Matériel", "display": "Matériel",
    "multimedia": "Matériel", "audio": "Matériel", "power-management": "Énergie",
    "removable_devices": "Matériel", "printers": "Matériel",
    "system-administration": "Système", "session": "Système", "security-privacy": "Sécurité et confidentialité",
    "infos": "Informations",
}


class KcmPage(QWidget):
    """Un module de réglage KDE affiché dans Paramètres, avec ses boutons."""

    def __init__(self, kcm_id, title, icon_pm, back=None):
        super().__init__()
        self.title = title
        self.kcm_id = kcm_id
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        head = QWidget()
        head.setObjectName("NPage")
        hl = QHBoxLayout(head)
        hl.setContentsMargins(24, 16, 24, 10)
        if back:
            hl.addWidget(button("‹ Retour", "link", back))
        ic = QLabel()
        ic.setPixmap(icon_pm)
        hl.addWidget(ic)
        hl.addWidget(label(title, "h1"))
        hl.addStretch()
        v.addWidget(head)

        self.module = K.Module(kcm_id)
        if self.module.ok:
            body = QWidget()
            bl = QVBoxLayout(body)
            bl.setContentsMargins(12, 0, 12, 0)
            bl.addWidget(self.module.widget)
            v.addWidget(body, 1)

            bar = QWidget()
            bar.setObjectName("NPage")
            b = QHBoxLayout(bar)
            b.setContentsMargins(24, 10, 24, 14)
            self.b_def = button("Par défaut", None, self.module.par_defaut)
            self.b_reset = button("Rétablir", None, self.module.recharger)
            self.b_apply = button("Appliquer", "primary", self.module.enregistrer)
            b.addWidget(self.b_def)
            b.addStretch()
            b.addWidget(self.b_reset)
            b.addWidget(self.b_apply)
            v.addWidget(bar)
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._update_buttons)
            self._timer.start(400)
            self._update_buttons()
        else:
            # Pont indisponible ou module introuvable : ouverture dans une fenêtre à part
            box = QWidget()
            box.setObjectName("NPage")
            bl = QVBoxLayout(box)
            bl.setContentsMargins(24, 10, 24, 24)
            bl.addWidget(label("Ce réglage s'ouvre dans sa propre fenêtre.", "sub"))
            bl.addWidget(button(f"Ouvrir « {title} »", "primary", lambda: open_kcm(kcm_id)),
                         0, Qt.AlignmentFlag.AlignLeft)
            bl.addStretch()
            v.addWidget(box, 1)

    def _update_buttons(self):
        dirty = self.module.a_enregistrer()
        self.b_apply.setEnabled(dirty)
        self.b_reset.setEnabled(dirty)


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

        h.addWidget(side)

        self.stack = QStackedWidget()
        h.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.inline = None          # page de module ouverte depuis une autre page
        self.fill_list()
        self.select(start or "maj" if U.load_state().count else (start or "wifi"))
        # Mises à jour : la page et la pastille suivent le service en direct
        os.makedirs(U.CACHE_DIR, exist_ok=True)
        self.watch = QFileSystemWatcher([U.CACHE_DIR], self)
        if os.path.exists(U.STATE_FILE):
            self.watch.addPath(U.STATE_FILE)
        self.watch.directoryChanged.connect(self.on_state_changed)
        self.watch.fileChanged.connect(self.on_state_changed)
        self.badge_timer = QTimer(self)
        self.badge_timer.timeout.connect(self.on_state_changed)
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
        w.mouseReleaseEvent = lambda e: self.select("utilisateurs")
        return w

    def fill_list(self):
        self.list.clear()
        count = U.load_state().count
        first = True
        for group in SECTIONS:
            # module KDE non installé : pas d'entrée morte (ni de séparateur vide)
            group = [e for e in group if not e[5] or K.existe(e[5])]
            if not group:
                continue
            if not first:
                sep = QListWidgetItem()
                sep.setFlags(Qt.ItemFlag.NoItemFlags)
                sep.setSizeHint(QSize(10, 10))
                sep.setData(Qt.ItemDataRole.UserRole, None)
                self.list.addItem(sep)
            first = False
            for key, title, icon, color, glyph, kcm, desc, kw in group:
                it = QListWidgetItem(QIcon(real_icon(icon, 24, color, glyph, key)), title)
                it.setData(Qt.ItemDataRole.UserRole, key)
                it.setSizeHint(QSize(200, 34))
                if key == "maj" and count:
                    it.setData(Qt.ItemDataRole.UserRole + 1, count)
                self.list.addItem(it)

    def on_state_changed(self, *_):
        if os.path.exists(U.STATE_FILE) and U.STATE_FILE not in self.watch.files():
            self.watch.addPath(U.STATE_FILE)
        self.refresh_badge()
        if "maj" in self.pages:
            self._maj_refresh()

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
            it.setHidden(bool(t) and t_norm not in hay and key != "tous")
        if hasattr(self, "tous_filtre"):
            self.tous_filtre.setText(text)

    def select(self, key):
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.ItemDataRole.UserRole) == key:
                self.list.setCurrentRow(i)
                return

    def confirm_leave(self):
        """True si on peut quitter la page actuelle (changements appliqués ou abandonnés)."""
        cur = self.stack.currentWidget()
        if isinstance(cur, KcmPage) and cur.module and cur.module.a_enregistrer():
            r = QMessageBox.question(self, "Paramètres",
                                     f"Appliquer les changements de « {cur.title} » ?",
                                     QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Discard
                                     | QMessageBox.StandardButton.Cancel)
            if r == QMessageBox.StandardButton.Cancel:
                return False
            if r == QMessageBox.StandardButton.Apply:
                cur.module.enregistrer()
            else:
                cur.module.recharger()
        return True

    def on_select(self, cur, _prev):
        if not cur:
            return
        key = cur.data(Qt.ItemDataRole.UserRole)
        if key is None:
            return
        if not self.confirm_leave():
            self.list.blockSignals(True)
            self.list.setCurrentItem(_prev)
            self.list.blockSignals(False)
            return
        self.close_inline()
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
        return KcmPage(kcm, title, real_icon(icon, 32, color, glyph, key))

    def open_inline(self, kcm, title, icon_names="preferences-system"):
        """Ouvre un module KDE dans la fenêtre, avec « ‹ Retour » vers la page actuelle."""
        if not self.confirm_leave():
            return
        back_to = self.stack.currentWidget()
        self.close_inline()
        pg = KcmPage(kcm, title, real_icon(icon_names, 32), back=lambda: self.back_from_inline(back_to))
        self.inline = pg
        self.stack.addWidget(pg)
        self.stack.setCurrentWidget(pg)

    def back_from_inline(self, target):
        if not self.confirm_leave():
            return
        self.stack.setCurrentWidget(target)
        self.close_inline()

    def close_inline(self):
        if self.inline is not None:
            self.stack.removeWidget(self.inline)
            self.inline.deleteLater()
            self.inline = None

    # Tous les réglages ----------------------------------------------------------
    def page_tous(self):
        pg = page("Tous les réglages", "Chaque réglage du système, sans quitter Paramètres.")
        self.tous_filtre = QLineEdit()
        self.tous_filtre.setPlaceholderText("Rechercher un réglage")
        self.tous_filtre.setClearButtonEnabled(True)
        pg.body.addWidget(self.tous_filtre)
        mods = [m for m in K.liste() if not m.get("cache")]
        if not mods:
            pg.body.addWidget(label("La liste complète n'est pas disponible sur ce système.", "sub"))
            pg.body.addWidget(button("Ouvrir la configuration KDE", None, lambda: spawn(["systemsettings"])),
                              0, Qt.AlignmentFlag.AlignLeft)
            return finish(pg)
        groups = {}
        for m in mods:
            groups.setdefault(CATEGORIES.get(m.get("categorie") or "", "Autres réglages"), []).append(m)
        self._tous_rows = []
        for gname in sorted(groups, key=lambda g: (g == "Autres réglages", g == "Informations", g)):
            sec = label(gname.upper(), "section")
            pg.body.addWidget(sec)
            card = Card()
            for m in sorted(groups[gname], key=lambda m: m["nom"].lower()):
                r = SettingRow(m["nom"], m.get("description") or None, None,
                               real_icon(m.get("icone"), 28, GREY, m["nom"][:1]), chevron=True)
                r.clicked.connect(lambda m=m: self.open_inline(m["id"], m["nom"], m.get("icone") or ""))
                card.add(r)
                self._tous_rows.append((r, _strip_accents((m["nom"] + " " + (m.get("description") or "")
                                                            + " " + m["id"]).lower()), card, sec))
            pg.body.addWidget(card)

        def filtrer(text):
            t = _strip_accents(text.strip().lower())
            visible_cards = set()
            for r, hay, card, sec in self._tous_rows:
                show = not t or t in hay
                r.setVisible(show)
                if show:
                    visible_cards.add(id(card))
            for r, hay, card, sec in self._tous_rows:
                card.setVisible(id(card) in visible_cards)
                sec.setVisible(id(card) in visible_cards)
        self.tous_filtre.textChanged.connect(filtrer)
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
            r.clicked.connect(lambda: self.open_inline("kcm_networkmanagement", "Réseau", "preferences-system-network"))
            nets.add(r)
        pg.body.addWidget(nets)
        pg.body.addWidget(label("Pour vous connecter à un réseau protégé, cliquez dessus ou utilisez "
                                "l'icône réseau dans la barre.", "sub", wrap=True))
        pg.body.addWidget(button("Réglages réseau avancés…", None,
                                 lambda: self.open_inline("kcm_networkmanagement", "Réseau",
                                                          "preferences-system-network")),
                          0, Qt.AlignmentFlag.AlignLeft)
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
        rowb = QHBoxLayout()
        rowb.addWidget(button("Ajouter un appareil…", "primary", lambda: spawn(["bluedevil-wizard"])))
        rowb.addWidget(button("Réglages Bluetooth avancés…", None,
                              lambda: self.open_inline("kcm_bluetooth", "Bluetooth",
                                                       "preferences-system-bluetooth")))
        rowb.addStretch()
        wb = QWidget()
        wb.setLayout(rowb)
        pg.body.addWidget(wb)
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
                                 lambda: self.open_inline("kcm_pulseaudio", "Son : sorties et micros",
                                                          "preferences-desktop-sound")),
                          0, Qt.AlignmentFlag.AlignLeft)
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

        pg.body.addWidget(label("TEINTE", "section"))
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
        assortir = Toggle(read_conf("apparence.conf", {"assortir": "true"}).get("assortir") == "true")
        assortir.toggled.connect(lambda on: write_conf("apparence.conf", {"assortir": str(on).lower()}))
        acc.add(SettingRow("Assortir le fond d'écran", "Change aussi le fond selon la teinte choisie.", assortir))
        pg.body.addWidget(acc)

        more = Card()
        for t, k in (("Polices", "kcm_fonts"), ("Icônes", "kcm_icons"), ("Pointeur de la souris", "kcm_cursortheme")):
            r = SettingRow(t, None, chevron=True)
            r.clicked.connect(lambda k=k, t=t: self.open_inline(k, t))
            more.add(r)
        pg.body.addWidget(more)
        return finish(pg)

    def _set_theme(self, dark):
        accent = read_conf("apparence.conf", {"accent": HONEY}).get("accent")
        apply_color_scheme(dark, accent)
        write_conf("apparence.conf", {"theme": "sombre" if dark else "clair"})

    def _set_accent(self, col):
        write_conf("apparence.conf", {"accent": col})
        apply_accent(col)
        conf = read_conf("apparence.conf", {"assortir": "true", "fond": "image"})
        if conf.get("assortir") != "true":
            return
        nom = teinte_de(col)
        if conf.get("fond") == "anime":
            fond_anime(nom)
        else:
            d = os.path.join(WALLPAPERS, "NounoursOS" if nom == "Miel" else "NounoursOS-" + nom)
            if os.path.isdir(d):
                spawn(["plasma-apply-wallpaperimage", d])

    # Fond d'écran ---------------------------------------------------------------
    def page_fond(self):
        pg = page("Fond d'écran")
        anime = Card()
        conf = read_conf("apparence.conf", {"fond": "image", "accent": HONEY})
        t = Toggle(conf.get("fond") == "anime")

        def basculer(on):
            write_conf("apparence.conf", {"fond": "anime" if on else "image"})
            fond_anime(teinte_de(read_conf("apparence.conf", {"accent": HONEY}).get("accent")), on)
        t.toggled.connect(basculer)
        anime.add(SettingRow("Fond animé NounoursOS", "Lumières qui dérivent doucement aux couleurs de votre "
                             "teinte. Choisir une image ci-dessous le désactive.", t,
                             real_icon("", 30, key="fond")))
        self._fond_toggle = t
        pg.body.addWidget(anime)
        pg.body.addWidget(label("IMAGES", "section"))
        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setSpacing(14)
        grp = QButtonGroup(self)
        for i, (name, target, thumb) in enumerate(self._wallpapers()):
            c = ChoiceCard(name, QPixmap(thumb), w=196, h=112)
            c.clicked.connect(lambda _=False, t=target: self._set_image(t))
            grp.addButton(c)
            grid.addWidget(c, i // 3, i % 3)
        pg.body.addWidget(grid_w)
        pg.body.addWidget(button("Ajouter une photo…", None, self._pick_wallpaper), 0, Qt.AlignmentFlag.AlignLeft)
        return finish(pg)

    def _set_image(self, chemin):
        write_conf("apparence.conf", {"fond": "image"})
        self._fond_toggle.blockSignals(True)
        self._fond_toggle.setChecked(False)
        self._fond_toggle.blockSignals(False)
        spawn(["plasma-apply-wallpaperimage", chemin])

    def _wallpapers(self):
        out = []
        for d in sorted(glob.glob(os.path.join(WALLPAPERS, "*"))):
            if os.path.isdir(d):
                imgs = sorted(glob.glob(os.path.join(d, "contents", "images", "*")))
                shot = os.path.join(d, "contents", "screenshot.png")
                thumb = shot if os.path.exists(shot) else (imgs[0] if imgs else None)
                if thumb:
                    out.append((os.path.basename(d).replace("NounoursOS-", ""), d, thumb))
            elif d.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                out.append((os.path.splitext(os.path.basename(d))[0], d, d))
        out.sort(key=lambda x: x[0] != "NounoursOS")
        return out[:24]

    def _pick_wallpaper(self):
        from PyQt6.QtWidgets import QFileDialog
        f, _ = QFileDialog.getOpenFileName(self, "Choisir une image", os.path.expanduser("~/Images"),
                                           "Images (*.png *.jpg *.jpeg *.webp)")
        if f:
            self._set_image(f)

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

        pg.body.addWidget(label("SUR LE BUREAU", "section"))
        wid = Card()
        for plugin, titre, sous, y, w, h in (
                ("org.nounoursos.horloge", "Horloge", "Grande heure et date, en haut à droite", 2, 22, 10),
                ("org.nounoursos.moniteur", "Moniteur", "Processeur, mémoire, disque, température, réseau", 13, 18, 11)):
            present = DEMO or "true" in plasma_query(
                "print(desktops().some(function(d){ return d.widgets('%s').length > 0; }))" % plugin)
            t = Toggle(present)

            def basculer(on, plugin=plugin, y=y, w=w, h=h):
                if on:
                    plasma_script("desktops().forEach(function(d){ if (!d.widgets('%s').length) {"
                                  " var g = screenGeometry(d.screen); var u = gridUnit;"
                                  " d.addWidget('%s', g.width - (%d + 3) * u, %d * u, %d * u, %d * u); } })"
                                  % (plugin, plugin, w, y, w, h))
                else:
                    plasma_script("desktops().forEach(function(d){ d.widgets('%s').forEach("
                                  "function(x){ x.remove(); }); })" % plugin)
            t.toggled.connect(basculer)
            wid.add(SettingRow(titre, sous, t))
        pg.body.addWidget(wid)
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
        self.maj_btn = button("", "primary", self._maj_action)
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

    def _maj_action(self):
        if U.load_state().count:
            spawn(["nounoursos-maj"])
            return
        self.maj_title.setText("Recherche de mises à jour…")
        self.maj_sub.setText("Connexion aux serveurs NounoursOS et Debian.")
        self.maj_btn.setEnabled(False)
        self._maj_th = CheckThread()
        self._maj_th.done.connect(lambda _s: (self.maj_btn.setEnabled(True), self._maj_refresh(),
                                              self.refresh_badge()))
        self._maj_th.etape.connect(self.maj_sub.setText)
        self._maj_th.start()

    def _maj_refresh(self):
        s = U.load_state()
        rel = os_release()
        if s.error and not s.count:
            self.maj_title.setText("Impossible de vérifier les mises à jour")
            self.maj_sub.setText(s.error)
            self.maj_btn.setText("Réessayer")
        elif s.count:
            self.maj_title.setText(s.headline() + " est disponible")
            self.maj_sub.setText(s.summary() + ("\nRecommandé : contient des correctifs de sécurité."
                                                if s.security_count else ""))
            self.maj_btn.setText("Mettre à jour maintenant…")
        else:
            self.maj_title.setText("NounoursOS est à jour")
            self.maj_sub.setText(f"NounoursOS {rel.get('VERSION_ID', '')} « {rel.get('NOUNOURSOS_CODENAME', '')} »")
            self.maj_btn.setText("Rechercher des mises à jour")

    # Empreinte et visage ------------------------------------------------------------
    DOIGTS = [("right-index-finger", "Index droit"), ("right-middle-finger", "Majeur droit"),
              ("right-thumb", "Pouce droit"), ("left-index-finger", "Index gauche"),
              ("left-middle-finger", "Majeur gauche"), ("left-thumb", "Pouce gauche")]

    def page_empreinte(self):
        from PyQt6.QtWidgets import QComboBox
        pg = page("Empreinte et visage",
                  "Déverrouillez l'ordinateur et validez les demandes de mot de passe d'un simple doigt.")
        login, _ = user_info()
        info = "Lecteur détecté\n- #1 : Index droit" if DEMO else run(["fprintd-list", login], timeout=8)
        lecteur = bool(info) and "No devices" not in info and "Impossible" not in info
        enregistres = [nom for code, nom in self.DOIGTS if code in info]

        card = Card()
        etat = ("Aucun lecteur d'empreinte détecté sur cet ordinateur." if not lecteur else
                ("Empreintes enregistrées : " + ", ".join(enregistres)) if enregistres else
                "Lecteur prêt, aucune empreinte enregistrée.")
        card.add(SettingRow("Empreinte digitale", etat, None, real_icon("", 30, key="empreinte")))
        pg.body.addWidget(card)

        if lecteur:
            pg.body.addWidget(label("AJOUTER UNE EMPREINTE", "section"))
            enr = Card(margins=(16, 14, 16, 14))
            box = QWidget()
            v = QVBoxLayout(box)
            v.setContentsMargins(0, 0, 0, 0)
            row = QHBoxLayout()
            choix = QComboBox()
            for code, nom in self.DOIGTS:
                choix.addItem(nom, code)
            row.addWidget(choix)
            go = button("Enregistrer", "primary", None)
            row.addWidget(go)
            row.addStretch()
            v.addLayout(row)
            self.emp_msg = label("Posez puis levez le doigt plusieurs fois sur le lecteur quand c'est demandé.",
                                 "sub", wrap=True)
            v.addWidget(self.emp_msg)
            from PyQt6.QtWidgets import QProgressBar
            self.emp_prog = QProgressBar()
            self.emp_prog.setRange(0, 100)
            self.emp_prog.hide()
            v.addWidget(self.emp_prog)
            enr.add(box)
            pg.body.addWidget(enr)
            go.clicked.connect(lambda: self._enroler(choix.currentData(), go))
            if enregistres:
                pg.body.addWidget(button("Supprimer toutes mes empreintes", None,
                                         lambda: (spawn(["fprintd-delete", login]),
                                                  self.emp_msg.setText("Empreintes supprimées."))),
                                  0, Qt.AlignmentFlag.AlignLeft)

        pg.body.addWidget(label("UTILISER L'EMPREINTE POUR", "section"))
        usage = Card()
        pam_on = DEMO or "pam_fprintd" in open("/etc/pam.d/common-auth").read() \
            if os.path.exists("/etc/pam.d/common-auth") else False
        t = Toggle(pam_on)

        def set_pam(on):
            if not root_helper("empreinte-pam", "on" if on else "off"):
                t.blockSignals(True)
                t.setChecked(not on)
                t.blockSignals(False)
        t.toggled.connect(set_pam)
        usage.add(SettingRow("Ouverture de session et demandes de mot de passe",
                             "Connexion, sudo, installations… Le mot de passe reste toujours possible.", t))
        lock = SettingRow("Écran de verrouillage", "Réglé dans « Écran de verrouillage ».", None, chevron=True)
        lock.clicked.connect(lambda: self.select("verrouillage"))
        usage.add(lock)
        pg.body.addWidget(usage)

        pg.body.addWidget(label("RECONNAISSANCE DU VISAGE", "section"))
        face = Card()
        ft = Toggle(False)
        ft.setEnabled(False)
        face.add(SettingRow("Déverrouiller avec le visage",
                            "Nécessite une webcam infrarouge (type Windows Hello). Arrive dans une "
                            "prochaine version de NounoursOS.", ft))
        pg.body.addWidget(face)
        return finish(pg)

    def _enroler(self, doigt, bouton):
        login, _ = user_info()
        from PyQt6.QtCore import QProcess
        self.emp_prog.setValue(0)
        self.emp_prog.show()
        bouton.setEnabled(False)
        self.emp_msg.setText("Posez le doigt sur le lecteur…")
        proc = QProcess(self)
        self._emp_proc = proc
        etapes = {"n": 0}
        messages = {
            "enroll-stage-passed": "Bien ! Levez le doigt puis reposez-le.",
            "enroll-retry-scan": "Encore une fois, s'il vous plaît.",
            "enroll-swipe-too-short": "Glissez le doigt plus lentement.",
            "enroll-finger-not-centered": "Centrez le doigt sur le lecteur.",
            "enroll-remove-and-retry": "Levez le doigt et réessayez.",
            "enroll-duplicate": "Cette empreinte est déjà enregistrée.",
            "enroll-completed": "Empreinte enregistrée ✓",
            "enroll-failed": "L'enregistrement a échoué. Réessayez.",
        }

        def lire():
            for line in bytes(proc.readAllStandardOutput()).decode(errors="ignore").splitlines():
                for code, msg in messages.items():
                    if code in line:
                        self.emp_msg.setText(msg)
                        if code == "enroll-stage-passed":
                            etapes["n"] += 1
                            self.emp_prog.setValue(min(95, etapes["n"] * 12))
                        if code == "enroll-completed":
                            self.emp_prog.setValue(100)

        def fini(code, _st):
            bouton.setEnabled(True)
            if code != 0 and self.emp_prog.value() < 100:
                self.emp_msg.setText(messages["enroll-failed"])
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(lire)
        proc.finished.connect(fini)
        proc.start("fprintd-enroll", ["-f", doigt, login])

    # Écran de veille --------------------------------------------------------------
    def page_veille(self):
        pg = page("Écran de veille",
                  "Après quelques minutes sans activité : horloge, ourson et état de l'ordinateur. "
                  "Il ne se lance pas pendant une vidéo ou un jeu.")
        conf = read_conf("veille.conf", {"active": "true", "delai": "5"})
        card = Card()
        actif = Toggle(conf.get("active") == "true")
        card.add(SettingRow("Activer l'écran de veille", None, actif, real_icon("", 30, key="veille")))
        delai = QSlider(Qt.Orientation.Horizontal)
        delai.setRange(1, 60)
        delai.setValue(int(conf.get("delai", "5") or 5))
        delai.setFixedWidth(220)
        val = label(f"{delai.value()} min", "sub")
        box = QWidget()
        bl = QHBoxLayout(box)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(delai)
        bl.addWidget(val)
        card.add(SettingRow("Démarrer après", None, box))
        pg.body.addWidget(card)

        def enregistrer():
            write_conf("veille.conf", {"active": "true" if actif.isChecked() else "false",
                                       "delai": delai.value()})
            # Relance du service d'inactivité avec les nouveaux réglages
            spawn(["sh", "-c", "pkill -u \"$(id -u)\" -f 'swayidle -w timeout [0-9]+ nounoursos-veille'; "
                               "nounoursos-veille-service"])
        actif.toggled.connect(lambda _: enregistrer())
        delai.valueChanged.connect(lambda v: val.setText(f"{v} min"))
        delai.sliderReleased.connect(enregistrer)

        row = QHBoxLayout()
        row.addWidget(button("Aperçu", "primary", lambda: spawn(["nounoursos-veille"])))
        row.addWidget(label("Bougez la souris ou appuyez sur une touche pour quitter.", "sub"))
        row.addStretch()
        rw = QWidget()
        rw.setLayout(row)
        pg.body.addWidget(rw)
        pg.body.addWidget(label("Le verrouillage de la session (mot de passe) se règle dans "
                                "« Écran de verrouillage ».", "sub", wrap=True))
        return finish(pg)

    # Applications Windows (WinBoat) ---------------------------------------------------
    def page_windows(self):
        pg = page("Applications Windows",
                  "Deux façons de lancer vos logiciels Windows : directement avec la couche NT (Wine), "
                  "ou dans un vrai Windows avec WinBoat pour ceux qui résistent.")
        self._section_nt(pg)
        pg.body.addWidget(label("WINBOAT : UN VRAI WINDOWS", "section"))
        pg.body.addWidget(label("WinBoat fait tourner Windows en arrière-plan et affiche ses logiciels "
                                "dans des fenêtres NounoursOS, comme des applications normales.", "sub", wrap=True))
        checks = self._winboat_checks()
        card = Card()
        for title, ok, detail in checks:
            mark = label("✅" if ok else "⚠️")
            mark.setStyleSheet("font-size: 13pt;")
            card.add(SettingRow(title, detail, mark))
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

    def _wine(self):
        if DEMO:
            return "wine"
        for c in ("/opt/wine-stable/bin/wine", "/opt/wine-staging/bin/wine", "wine"):
            if shutil.which(c):
                return c
        return ""

    def _section_nt(self, pg):
        wine = self._wine()
        noyau = "7.3.4" if DEMO else os.uname().release.split("-")[0]
        ntsync = DEMO or os.path.exists("/dev/ntsync")
        version = "wine-11.0" if DEMO else (run([wine, "--version"], timeout=10).strip() if wine else "")
        pg.body.addWidget(label("COUCHE NT (WINE)", "section"))
        card = Card()

        def marque(t):
            m = label(t)
            m.setStyleSheet("font-size: 13pt;")
            return m
        card.add(SettingRow("Programmes Windows",
                            ("Les .exe et .msi s'ouvrent d'un double-clic (" + version + ")") if wine else
                            "Non installé : inclus dans l'édition NounoursOS NT.",
                            marque("✅" if wine else "⚠️"), real_icon("", 30, key="windows")))
        card.add(SettingRow("Synchronisation NT (ntsync)",
                            ("Active : les jeux et logiciels Windows tournent plus vite (noyau %s)" % noyau)
                            if ntsync else "Indisponible avec le noyau %s (6.14 ou plus récent requis)" % noyau,
                            marque("✅" if ntsync else "➖")))
        pg.body.addWidget(card)
        if not wine:
            return
        row = QHBoxLayout()
        row.addWidget(button("Ouvrir un programme Windows…", "primary", self._ouvrir_exe))
        row.addWidget(button("Lecteur C:", None, lambda: spawn(
            ["xdg-open", os.path.join(os.environ.get("WINEPREFIX", os.path.expanduser("~/.wine")), "drive_c")])))
        row.addWidget(button("Réglages Wine", None, lambda: spawn([wine.replace("/wine", "/winecfg")
                                                                  if wine.startswith("/") else "winecfg"])))
        row.addStretch()
        w = QWidget()
        w.setLayout(row)
        pg.body.addWidget(w)

    def _ouvrir_exe(self):
        from PyQt6.QtWidgets import QFileDialog
        f, _ = QFileDialog.getOpenFileName(self, "Programme Windows", os.path.expanduser("~/Téléchargements"),
                                           "Programmes Windows (*.exe *.msi *.bat *.lnk)")
        if f:
            spawn(["nounoursos-exe", f])

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
        infos = [m for m in K.liste() if m.get("categorie") == "infos"]
        row.addWidget(button("nounourscorp.fr", "link", lambda: spawn(["xdg-open", "https://nounourscorp.fr"])))
        row.addStretch()
        rw = QWidget()
        rw.setLayout(row)
        pg.body.addWidget(rw)
        if infos:
            pg.body.addWidget(label("INFORMATIONS DÉTAILLÉES", "section"))
            ic = Card()
            for m in sorted(infos, key=lambda m: m["nom"].lower()):
                r = SettingRow(m["nom"], None, None, real_icon(m.get("icone"), 24, GREY, "i"), chevron=True)
                r.clicked.connect(lambda m=m: self.open_inline(m["id"], m["nom"], m.get("icone") or ""))
                ic.add(r)
            pg.body.addWidget(ic)
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
    app.setStyleSheet(stylesheet(scoped=True))
    start = argv[0] if argv and argv[0] in ITEMS else None
    w = Settings(start)
    w.show()
    return app.exec()
