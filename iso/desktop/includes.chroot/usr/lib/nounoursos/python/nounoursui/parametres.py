"""Paramètres NounoursOS — TOUS les réglages au même endroit, façon macOS.

- Pages NounoursOS : Wi-Fi, Bluetooth, Son, Apparence, Fond d'écran, Bureau et
  Dock, Mise à jour, À propos, Applications Windows.
- Tous les autres réglages sont les modules KDE eux-mêmes, affichés DANS la
  fenêtre (via libnounoursos-kcm.so), avec Appliquer / Rétablir / Par défaut.
- « Tous les réglages » liste chaque module installé : rien n'oblige à sortir.
"""
import glob
import json
import os
import time
import re
import shutil
import socket
import sys

from PyQt6.QtCore import Qt, QSize, QRectF, QTimer, QFileSystemWatcher, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QListWidget, QListWidgetItem, QStackedWidget, QLineEdit, QLabel,
                             QScrollArea, QSlider, QGridLayout, QButtonGroup, QFrame,
                             QStyledItemDelegate, QStyle, QMessageBox)

from . import (label, button, Card, SettingRow, Toggle, ChoiceCard, Swatch, tile_icon,
               logo_pixmap, colors, stylesheet, run, spawn, has, open_kcm, root_helper,
               user_info, os_release, read_conf, write_conf, apply_color_scheme, apply_accent, fond_anime, teinte_de,
               plasma_script, plasma_query, is_dark, ACCENTS, HONEY, LNF, WALLPAPERS, DEMO, CONFIG_DIR, DATA, HELPER)
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
    [("compte", "NounoursAccount", "user-identity|im-user", HONEY, "N", None, "",
      "compte nounoursaccount connexion nounourscorp pieces profil sites"),
     ("maj", "Mise à jour", "system-software-update", GREY, "M", None, "", "mises a jour version securite"),
     ("capsule", "Capsule temporelle", "backup|document-save", TEAL, "C", None, "",
      "sauvegarde backup time machine restaurer disque externe fichiers perdus"),
     ("apropos", "À propos", "hwinfo|computer|help-about", GREY, "i", None, "",
      "version systeme info materiel"),
     ("windows", "Applications Windows", "winboat|computer", "#2F6FDB", "⊞", None, "",
      "winboat windows exe logiciels office photoshop"),
     ("jeu", "Mode jeu", "input-gaming|applications-games", GREEN, "J", None, "",
      "jeux steam gamemode proton pilote nvidia vulkan manette"),
     ("concentration", "Concentration", "preferences-desktop-notification-bell|notifications-disabled", "#5B5BD6",
      "C", None, "", "ne pas deranger focus travail jeu stream notifications horaire mode"),
     ("telephone", "Téléphone", "kdeconnect|smartphone|phone", GREEN, "T", "kcm_kdeconnect", "",
      "iphone android kde connect sms notifications fichiers partage"),
     ("partage", "Partage de fichiers", "document-send|folder-network", BLUE, "P", None, "",
      "airdrop localsend envoyer fichiers iphone mac windows android partager"),
     ("nettoyage", "Nettoyage", "edit-clear-all|user-trash-full", TEAL, "N", None, "",
      "espace disque plein libérer cache corbeille stockage")],
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
            f = QFont("Inter", 8)
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
    p.fillRect(QRectF(0, h - 18, w, 18), QColor("#1B1329" if dark else "#FFFFFF"))
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
        carte = self.user_card()
        carte.setObjectName("CarteCompte")
        sv.addWidget(carte)
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
        from . import compte
        login, full = user_info()
        na = compte.utilisateur() or ({"name": "Camille", "username": "camille"} if DEMO else None)
        w = QFrame()
        w.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 6, 6, 6)
        av = QLabel()
        face = os.path.expanduser("~/.face.icon")
        if na and os.path.exists(compte.AVATAR):
            face = compte.AVATAR
        if os.path.exists(face):
            pm = QPixmap(face).scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                      Qt.TransformationMode.SmoothTransformation)
        else:
            pm = tile_icon(None, HONEY, 44, ((na or {}).get("name") or full or login)[:1].upper())
        av.setPixmap(pm)
        lay.addWidget(av)
        v = QVBoxLayout()
        v.setSpacing(0)
        n = label((na or {}).get("name") or full)
        n.setStyleSheet("font-weight: 700; font-size: 10.5pt;")
        v.addWidget(n)
        v.addWidget(label("NounoursAccount · @" + na.get("username", "") if na else
                          "Se connecter à NounoursAccount", "sub"))
        lay.addLayout(v, 1)
        w.mouseReleaseEvent = lambda e: self.select("compte")
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

    def open_page(self, key):
        """Reconstruit une page (après un changement qui modifie son contenu) et l'affiche."""
        old = self.pages.pop(key, None)
        if old is not None:
            self.stack.removeWidget(old)
            old.deleteLater()
        self.pages[key] = self.build(key)
        self.stack.addWidget(self.pages[key])
        self.stack.setCurrentWidget(self.pages[key])

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

    # Modes Concentration ----------------------------------------------------------------
    APPLIS_MODE = {"jeu": [("steam.desktop", "Ouvrir Steam")],
                   "stream": [("com.obsproject.Studio.desktop", "Ouvrir OBS Studio")],
                   "travail": []}

    def page_concentration(self):
        from . import concentration as C
        from PyQt6.QtWidgets import QTimeEdit, QFileDialog
        from PyQt6.QtCore import QTime
        pg = page("Concentration", "Un clic pour couper les notifications et préparer l'ordinateur selon ce que "
                                   "vous faites. Aussi dans le Centre de contrôle, en haut à droite.")
        d = C.lire()
        for cle, m in d["modes"].items():
            pg.body.addWidget(label(f"{m.get('icone', '')}  {m['nom'].upper()}", "section"))
            card = Card()
            actif = Toggle(d["actif"] == cle)
            actif.toggled.connect(lambda on, k=cle: (C.activer(k if on else None), self.open_page("concentration")))
            card.add(SettingRow(f"Mode {m['nom']}", "Actif en ce moment" if d["actif"] == cle else "Inactif",
                                actif))
            ndp = Toggle(m.get("ne_pas_deranger", True))
            ndp.toggled.connect(lambda on, k=cle: C.regler(k, ne_pas_deranger=on))
            card.add(SettingRow("Ne pas déranger", "Aucune notification tant que le mode est actif.", ndp))
            for appli, texte in self.APPLIS_MODE.get(cle, []):
                if not (DEMO or os.path.exists(os.path.join("/usr/share/applications", appli))
                        or os.path.exists(os.path.join("/var/lib/flatpak/exports/share/applications", appli))):
                    continue
                t = Toggle(appli in m.get("applis", []))
                t.toggled.connect(lambda on, k=cle, a=appli: C.regler(
                    k, applis=sorted(set(C.lire()["modes"][k].get("applis", [])) ^ {a})))
                card.add(SettingRow(texte, "À l'activation du mode.", t))
            fond = m.get("fond", "")
            rf = SettingRow("Fond d'écran du mode", os.path.basename(fond) if fond else
                            "Aucun changement (cliquez pour en choisir un)", None, chevron=True)

            def choisir(k=cle):
                f, _ = QFileDialog.getOpenFileName(self, "Fond d'écran du mode", WALLPAPERS,
                                                   "Images (*.png *.jpg *.jpeg *.webp)")
                C.regler(k, fond=f or "")
                self.open_page("concentration")
            rf.clicked.connect(choisir)
            card.add(rf)
            h = m.get("horaire", {})
            box = QWidget()
            row = QHBoxLayout(box)
            row.setContentsMargins(0, 0, 0, 0)
            auto = Toggle(h.get("actif", False))
            debut, fin = QTimeEdit(QTime.fromString(h.get("debut", "09:00"), "HH:mm")), \
                QTimeEdit(QTime.fromString(h.get("fin", "17:00"), "HH:mm"))
            for te in (debut, fin):
                te.setDisplayFormat("HH:mm")
            semaine = Toggle(h.get("jours") == [1, 2, 3, 4, 5])

            def sauver(_=None, k=cle, auto=auto, debut=debut, fin=fin, semaine=semaine):
                C.regler(k, horaire={"actif": auto.isChecked(), "debut": debut.time().toString("HH:mm"),
                                     "fin": fin.time().toString("HH:mm"),
                                     "jours": [1, 2, 3, 4, 5] if semaine.isChecked() else [1, 2, 3, 4, 5, 6, 7]})
            for wdg in (auto, semaine):
                wdg.toggled.connect(sauver)
            for te in (debut, fin):
                te.timeChanged.connect(sauver)
            row.addWidget(label("de"))
            row.addWidget(debut)
            row.addWidget(label("à"))
            row.addWidget(fin)
            row.addSpacing(10)
            row.addWidget(label("en semaine seulement"))
            row.addWidget(semaine)
            row.addSpacing(10)
            row.addWidget(auto)
            card.add(SettingRow("Automatiquement", None, box))
            pg.body.addWidget(card)
        return finish(pg)

    # NounoursAccount -----------------------------------------------------------------------
    def page_compte(self):
        from . import compte
        pg = page("NounoursAccount", "Votre compte NounoursCorp, le même que sur les sites et NounoursLauncher.")
        user = compte.utilisateur() or ({"name": "Camille", "username": "camille", "coins": 120} if DEMO else None)
        card = Card(margins=(18, 16, 18, 16))
        if user:
            box = QWidget()
            h = QHBoxLayout(box)
            h.setContentsMargins(0, 0, 0, 0)
            av = QLabel()
            pm = QPixmap(compte.AVATAR) if os.path.exists(compte.AVATAR) else \
                tile_icon(None, HONEY, 64, (user.get("name") or "?")[:1].upper())
            av.setPixmap(pm.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                   Qt.TransformationMode.SmoothTransformation))
            h.addWidget(av)
            v = QVBoxLayout()
            v.addWidget(label(user.get("name") or user.get("username", ""), "h2"))
            v.addWidget(label(f"@{user.get('username', '')}" + (" · administrateur" if user.get("admin") else ""),
                              "sub"))
            if user.get("coins") is not None:
                v.addWidget(label(f"🪙 {user['coins']} pièces", "sub"))
            h.addLayout(v, 1)
            card.add(box)
            pg.body.addWidget(card)
            pg.body.addWidget(label("VOS SITES", "section"))
            sites = Card()
            for nom, url in compte.SITES:
                r = SettingRow(nom, url.replace("https://", "").rstrip("/"), None, chevron=True)
                r.clicked.connect(lambda u=url: spawn(["xdg-open", u]))
                sites.add(r)
            pg.body.addWidget(sites)
            pg.body.addWidget(button("Se déconnecter de cet ordinateur", None, lambda: (
                compte.deconnecter(), self._rafraichir_compte())), 0, Qt.AlignmentFlag.AlignLeft)
            return finish(pg)

        card.add(SettingRow("Pas encore connecté", "Connectez-vous pour retrouver votre profil, vos pièces et "
                            "un accès direct à vos sites NounoursCorp.", None, real_icon("", 30, key="compte")))
        pg.body.addWidget(card)
        self.na_btn = button("Se connecter avec NounoursAccount", "primary", self._compte_commencer)
        pg.body.addWidget(self.na_btn, 0, Qt.AlignmentFlag.AlignLeft)
        self.na_code = label("", "title", align=Qt.AlignmentFlag.AlignCenter)
        self.na_code.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.na_code.hide()
        pg.body.addWidget(self.na_code)
        self.na_msg = label("", "sub", wrap=True)
        pg.body.addWidget(self.na_msg)
        return finish(pg)

    def _rafraichir_compte(self):
        self.open_page("compte")
        old = self.findChild(QFrame, "CarteCompte")
        if old is not None:
            nouveau = self.user_card()
            nouveau.setObjectName("CarteCompte")
            old.parentWidget().layout().replaceWidget(old, nouveau)
            old.deleteLater()

    def _compte_commencer(self):
        from . import compte
        if DEMO:
            self.na_code.setText("K7QM-2XPA")
            self.na_code.show()
            self.na_msg.setText("[démo] Ouvrez nounourscorp.fr/launcher/connect.php et saisissez ce code.")
            return
        self.na_btn.setEnabled(False)
        self.na_msg.setText("Connexion à NounoursAccount…")
        try:
            d = compte.commencer()
        except compte.ErreurCompte as e:
            self.na_btn.setEnabled(True)
            self.na_msg.setText(str(e))
            return
        self.na_code.setText(d["code"])
        self.na_code.show()
        self.na_msg.setText("Une page de connexion s'ouvre dans le navigateur : validez-y ce code (déjà connecté "
                            "à NounoursAccount ? un clic suffit). Le code est valable 10 minutes.")
        spawn(["xdg-open", d["url"]])
        self._na_poll = d["poll"]
        self._na_essais = int(d.get("expires_in", 600)) // 3
        self._na_timer = QTimer(self)
        self._na_timer.timeout.connect(self._compte_verifier)
        self._na_timer.start(3000)

    def _compte_verifier(self):
        from . import compte
        self._na_essais -= 1
        try:
            user = compte.verifier(self._na_poll)
        except compte.ErreurCompte as e:
            self._na_timer.stop()
            self.na_btn.setEnabled(True)
            self.na_code.hide()
            self.na_msg.setText(str(e))
            return
        if user:
            self._na_timer.stop()
            self._rafraichir_compte()
        elif self._na_essais <= 0:
            self._na_timer.stop()
            self.na_btn.setEnabled(True)
            self.na_code.hide()
            self.na_msg.setText("Le code a expiré. Recommencez la connexion.")

    # Partage de fichiers (LocalSend) ------------------------------------------------------
    @staticmethod
    def _localsend_desktop():
        for d in ("/usr/share/applications", os.path.expanduser("~/.local/share/applications")):
            try:
                for f in sorted(os.listdir(d)):
                    if f.endswith(".desktop") and "localsend" in f.lower():
                        return os.path.join(d, f)
            except OSError:
                pass
        return "/usr/share/applications/localsend_app.desktop" if DEMO else None

    def page_partage(self):
        pg = page("Partage de fichiers",
                  "Envoyez photos, vidéos et documents entre NounoursOS, votre iPhone, votre Mac, un PC Windows "
                  "ou un téléphone Android, comme avec AirDrop. Tout passe par votre réseau Wi-Fi, sans Internet "
                  "ni compte.")
        bureau = self._localsend_desktop()
        card = Card()
        card.add(SettingRow("LocalSend", "Installé et prêt" if bureau else
                            "Pas installé : il arrive avec les mises à jour de NounoursOS.",
                            None, real_icon("", 30, key="partage")))
        if bureau:
            auto = os.path.join(os.path.expanduser("~/.config/autostart"), os.path.basename(bureau))
            t = Toggle(os.path.exists(auto))

            def demarrage(on):
                if on:
                    os.makedirs(os.path.dirname(auto), exist_ok=True)
                    with open(bureau) as f:
                        txt = f.read()
                    # Démarre discrètement dans la zone de notification pour pouvoir recevoir
                    txt = re.sub(r"^Exec=(\S+).*$", r"Exec=\1 --hidden", txt, count=1, flags=re.M)
                    with open(auto, "w") as f:
                        f.write(txt)
                elif os.path.exists(auto):
                    os.unlink(auto)
            t.toggled.connect(demarrage)
            card.add(SettingRow("Pouvoir recevoir à tout moment",
                                "LocalSend démarre avec l'ordinateur, discrètement, pour accepter les envois.", t))
        pg.body.addWidget(card)
        if bureau:
            pg.body.addWidget(button("Ouvrir LocalSend", "primary", lambda: spawn(["kioclient", "exec", bureau])),
                              0, Qt.AlignmentFlag.AlignLeft)
        pg.body.addWidget(label("SUR VOS AUTRES APPAREILS", "section"))
        aide = Card()
        for titre, detail in (("iPhone et iPad", "Installez « LocalSend » depuis l'App Store."),
                              ("Mac", "Installez « LocalSend » depuis l'App Store ou localsend.org."),
                              ("Windows et Android", "Installez « LocalSend » depuis le Microsoft Store, "
                                                     "le Play Store ou localsend.org.")):
            aide.add(SettingRow(titre, detail, None))
        pg.body.addWidget(aide)
        pg.body.addWidget(label("Les appareils doivent être sur le même réseau Wi-Fi. Ils apparaissent tout seuls "
                                "dans LocalSend : choisissez-en un, puis les fichiers à envoyer.", "sub", wrap=True))
        return finish(pg)

    # Mode jeu ----------------------------------------------------------------------------
    def page_jeu(self):
        from PyQt6.QtWidgets import QProgressBar
        pg = page("Mode jeu", "Steam, les jeux Windows grâce à Proton, et un ordinateur qui donne tout "
                              "pendant que vous jouez.")
        gpu = "AMD Radeon RX 6600" if DEMO else ""
        if not DEMO:
            for line in run(["lspci"], timeout=5).splitlines():
                if re.search(r"VGA|3D|Display", line):
                    gpu = line.split(": ", 1)[-1]
                    gpu = re.sub(r"\s*\(rev .*\)$", "", gpu)
                    break
        nvidia = "nvidia" in gpu.lower()
        verifs = [
            ("Steam", DEMO or bool(shutil.which("steam")), "Installé" if DEMO or shutil.which("steam")
             else "Pas encore installé"),
            ("GameMode", DEMO or bool(shutil.which("gamemoded")),
             "Donne la priorité au jeu pendant qu'il tourne"),
            ("Jeux 32 bits (Vulkan)", DEMO or os.path.exists("/usr/lib/i386-linux-gnu/libvulkan.so.1"),
             "Nécessaire à beaucoup de jeux Windows"),
            ("Carte graphique", True, gpu or "Inconnue"),
        ]
        if nvidia:
            verifs.append(("Pilote NVIDIA", bool(shutil.which("nvidia-smi")), "Pilote officiel, plus rapide"))
        if os.path.exists("/dev/ntsync") or DEMO:
            verifs.append(("Synchronisation NT (ntsync)", True, "Proton l'utilise : jeux Windows plus fluides"))
        card = Card()
        for titre, ok, detail in verifs:
            m = label("✅" if ok else "⚠️")
            m.setStyleSheet("font-size: 13pt;")
            card.add(SettingRow(titre, detail, m))
        pg.body.addWidget(card)
        manque = [t for t, ok, _ in verifs if not ok]
        row = QHBoxLayout()
        if manque:
            self.jeu_btn = button("Installer le mode jeu", "primary", None)
            self.jeu_btn.clicked.connect(self._installer_jeu)
            row.addWidget(self.jeu_btn)
        if DEMO or shutil.which("steam"):
            row.addWidget(button("Ouvrir Steam", None if manque else "primary", lambda: spawn(["steam"])))
        row.addStretch()
        w = QWidget()
        w.setLayout(row)
        pg.body.addWidget(w)
        self.jeu_prog = QProgressBar()
        self.jeu_prog.setRange(0, 100)
        self.jeu_prog.hide()
        pg.body.addWidget(self.jeu_prog)
        self.jeu_msg = label(
            "Un clic installe Steam, GameMode et les bibliothèques des jeux (environ 1 Go)"
            + (", ainsi que le pilote NVIDIA." if nvidia else ".") if manque else
            "Pour les jeux Windows, activez Proton dans Steam › Paramètres › Compatibilité. Astuce : "
            "ajoutez « gamemoderun %command% » aux options de lancement d'un jeu.", "sub", wrap=True)
        pg.body.addWidget(self.jeu_msg)
        return finish(pg)

    def _installer_jeu(self):
        from PyQt6.QtCore import QProcess
        self.jeu_btn.setEnabled(False)
        self.jeu_prog.setValue(0)
        self.jeu_prog.show()
        self.jeu_msg.setText("Installation… (environ 1 Go à télécharger)")
        proc = QProcess(self)
        self._jeu_proc = proc

        def lire():
            for line in bytes(proc.readAllStandardOutput()).decode(errors="ignore").splitlines():
                parts = line.split(":")
                if line.startswith("dlstatus:") and len(parts) > 2:
                    self.jeu_prog.setValue(int(float(parts[2]) * 0.4))
                    self.jeu_msg.setText("Téléchargement…")
                elif line.startswith("pmstatus:") and len(parts) > 2:
                    self.jeu_prog.setValue(40 + int(float(parts[2]) * 0.6))
                    self.jeu_msg.setText("Installation de " + parts[1] + "…")

        def fini(code, _st):
            self.jeu_prog.hide()
            if code == 0:
                self.jeu_msg.setText("Mode jeu installé. Bon jeu !")
                self.open_page("jeu")
            else:
                self.jeu_btn.setEnabled(True)
                self.jeu_msg.setText("L'installation n'a pas abouti (journal : /var/log/nounoursos/mode-jeu.log).")
        proc.readyReadStandardOutput.connect(lire)
        proc.finished.connect(fini)
        proc.start("pkexec", [HELPER, "mode-jeu"])

    # Nettoyage --------------------------------------------------------------------------
    GARDER_CACHE = ("nounoursos", "fontconfig", "ksycoca6", "plasmashell", "kwin", "plasma_theme")

    def _taille(self, chemin):
        total = 0
        for racine, _d, fichiers in os.walk(chemin):
            for f in fichiers:
                try:
                    total += os.lstat(os.path.join(racine, f)).st_size
                except OSError:
                    pass
        return total

    def page_nettoyage(self):
        pg = page("Nettoyage", "Libérez de la place sans toucher à vos documents.")
        home = os.path.expanduser("~")
        du = shutil.disk_usage(home)
        g = 2 ** 30
        card = Card(margins=(18, 14, 18, 16))
        barre = QWidget()
        v = QVBoxLayout(barre)
        v.setContentsMargins(0, 0, 0, 0)
        utilise = (du.total - du.free) / du.total if du.total else 0
        v.addWidget(label(f"{du.free / g:.0f} Go libres sur {du.total / g:.0f} Go", "h2"))
        from PyQt6.QtWidgets import QProgressBar
        b = QProgressBar()
        b.setRange(0, 1000)
        b.setValue(int(utilise * 1000))
        b.setTextVisible(False)
        v.addWidget(b)
        card.add(barre)
        pg.body.addWidget(card)

        cache = os.path.join(home, ".cache")
        corbeille = os.path.join(home, ".local/share/Trash")
        if DEMO:
            tailles = {"cache": 2.4 * g, "corbeille": 860 * 2 ** 20, "apt": 1.1 * g, "journal": 412 * 2 ** 20}
        else:
            tailles = {
                "cache": sum(self._taille(os.path.join(cache, n)) for n in os.listdir(cache)
                             if n not in self.GARDER_CACHE) if os.path.isdir(cache) else 0,
                "corbeille": self._taille(corbeille),
                "apt": self._taille("/var/cache/apt/archives"),
                "journal": 0,
            }
            m = re.search(r"take up ([\d.]+)([KMGT])", run(["journalctl", "--disk-usage"], timeout=10))
            if m:
                tailles["journal"] = float(m.group(1)) * {"K": 2 ** 10, "M": 2 ** 20, "G": g, "T": 2 ** 40}[m.group(2)]

        def taille_txt(n):
            return f"{n / g:.1f} Go".replace(".", ",") if n >= g / 2 else f"{n / 2 ** 20:.0f} Mo"

        pg.body.addWidget(label("CE QUI PEUT PARTIR", "section"))
        lst = Card()
        self.net_lignes = {}
        for cle, titre, detail in (
                ("corbeille", "Corbeille", "Les fichiers que vous avez supprimés"),
                ("cache", "Caches des applications", "Miniatures, caches du navigateur… recréés au besoin"),
                ("apt", "Paquets téléchargés", "Restes des mises à jour, plus utiles une fois installés"),
                ("journal", "Anciens journaux du système", "On garde les 200 Mo les plus récents")):
            bt = button(f"Libérer {taille_txt(tailles[cle])}", None, None)
            bt.setEnabled(tailles[cle] > 1024 * 1024)
            bt.clicked.connect(lambda _=False, c=cle, bt=bt: self._nettoyer(c, bt))
            self.net_lignes[cle] = bt
            lst.add(SettingRow(titre, detail, bt))
        pg.body.addWidget(lst)
        self.net_msg = label("Les paquets et les journaux demandent le mot de passe administrateur une fois.",
                             "sub", wrap=True)
        pg.body.addWidget(self.net_msg)
        gros = SettingRow("Voir ce qui prend de la place", "Explorer le disque dossier par dossier", None,
                          chevron=True)
        gros.clicked.connect(lambda: spawn(["filelight", home] if shutil.which("filelight")
                                           else ["dolphin", home]))
        c2 = Card()
        c2.add(gros)
        pg.body.addWidget(c2)
        return finish(pg)

    def _nettoyer(self, cle, bouton):
        home = os.path.expanduser("~")
        if DEMO:
            bouton.setText("Fait ✓")
            bouton.setEnabled(False)
            return
        if cle == "corbeille":
            for sous in ("files", "info", "expunged"):
                d = os.path.join(home, ".local/share/Trash", sous)
                if os.path.isdir(d):
                    for n in os.listdir(d):
                        p = os.path.join(d, n)
                        shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) and not os.path.islink(p) \
                            else os.unlink(p)
        elif cle == "cache":
            cache = os.path.join(home, ".cache")
            for n in os.listdir(cache):
                if n in self.GARDER_CACHE:
                    continue
                p = os.path.join(cache, n)
                try:
                    shutil.rmtree(p) if os.path.isdir(p) and not os.path.islink(p) else os.unlink(p)
                except OSError:
                    pass
        else:
            if not root_helper("nettoyage-systeme"):
                self.net_msg.setText("Nettoyage annulé.")
                return
            for c in ("apt", "journal"):
                self.net_lignes[c].setText("Fait ✓")
                self.net_lignes[c].setEnabled(False)
        bouton.setText("Fait ✓")
        bouton.setEnabled(False)

    # Capsule temporelle ----------------------------------------------------------------
    def page_capsule(self):
        from . import capsule as C
        from PyQt6.QtWidgets import QProgressBar, QFileDialog
        pg = page("Capsule temporelle",
                  "Une sauvegarde de vos fichiers toutes les heures. Un fichier supprimé ou abîmé ? "
                  "Retrouvez-le tel qu'il était hier, la semaine dernière ou le mois dernier.")
        conf = C.lire_conf()
        etat = C.lire_etat()
        dest = conf.get("destination", "")
        snaps = C.liste(dest) if not DEMO else [(time.time() - h * 3600, f"/media/demo/{h}")
                                                  for h in (0, 1, 2, 26, 50, 24 * 9)]

        # État
        card = Card()
        if DEMO:
            etat = {"derniere": time.time() - 1500, "ok": True}
            dest = dest or "/media/nounours/Sauvegardes"
        if etat.get("ok") is False and etat.get("message"):
            txt = etat["message"]
        elif etat.get("derniere"):
            txt = "Dernière sauvegarde : " + C.libelle(etat["derniere"])
        else:
            txt = "Aucune sauvegarde pour le moment."
        self.caps_etat = SettingRow("Sauvegarder automatiquement", txt,
                                    Toggle(conf.get("active") == "true" or DEMO), real_icon("", 30, key="capsule"))
        auto = self.caps_etat.findChild(Toggle)

        def basculer(on):
            if on and not (dest or C.lire_conf().get("destination")):
                auto.blockSignals(True)
                auto.setChecked(False)
                auto.blockSignals(False)
                self.caps_msg.setText("Choisissez d'abord un disque ci-dessous.")
                return
            C.ecrire_conf(active=str(on).lower())
            spawn(["systemctl", "--user", "enable" if on else "disable", "--now", "nounoursos-capsule.timer"])
        auto.toggled.connect(basculer)
        card.add(self.caps_etat)
        pg.body.addWidget(card)

        # Sauvegarder maintenant
        row = QHBoxLayout()
        self.caps_btn = button("Sauvegarder maintenant", "primary", None)
        self.caps_btn.setEnabled(bool(dest))
        row.addWidget(self.caps_btn)
        self.caps_prog = QProgressBar()
        self.caps_prog.setRange(0, 100)
        self.caps_prog.setMaximumWidth(260)
        self.caps_prog.hide()
        row.addWidget(self.caps_prog)
        self.caps_msg = label("", "sub")
        row.addWidget(self.caps_msg, 1)
        w = QWidget()
        w.setLayout(row)
        pg.body.addWidget(w)
        self.caps_btn.clicked.connect(self._capsule_maintenant)

        # Disque
        pg.body.addWidget(label("DISQUE DE SAUVEGARDE", "section"))
        dcard = Card()
        disques = C.disques_externes() if not DEMO else [("Sauvegardes", "/media/nounours/Sauvegardes",
                                                            412 * 2 ** 30, 1000 * 2 ** 30)]
        for nom, chemin, libre, total in disques:
            actuel = os.path.realpath(chemin) == os.path.realpath(dest) if dest else False
            choisir = label("✓ Utilisé", "sub") if actuel else button("Utiliser", None, None)
            if not actuel:
                choisir.clicked.connect(lambda _=False, c=chemin: self._capsule_destination(c))
            dcard.add(SettingRow(nom, f"{libre / 2 ** 30:.0f} Go libres sur {total / 2 ** 30:.0f} Go",
                                 choisir, real_icon("", 26, key="disques")))
        if not disques:
            dcard.add(SettingRow("Aucun disque externe branché",
                                 "Branchez un disque USB, il apparaîtra ici. Vous pouvez aussi choisir un dossier.",
                                 None))
        autre = SettingRow("Choisir un dossier…", dest if dest and not any(
            os.path.realpath(c) == os.path.realpath(dest) for _, c, _, _ in disques) else
            "Un disque réseau, une deuxième partition…", None, chevron=True)
        autre.clicked.connect(lambda: (lambda d: d and self._capsule_destination(d))(
            QFileDialog.getExistingDirectory(self, "Dossier de sauvegarde", "/media")))
        dcard.add(autre)
        pg.body.addWidget(dcard)
        if dest and not DEMO and os.path.isdir(dest):
            home_dev = os.stat(os.path.expanduser("~")).st_dev
            if os.stat(dest).st_dev == home_dev:
                pg.body.addWidget(label("⚠️ Ce dossier est sur le même disque que vos fichiers : il protège des "
                                        "erreurs, mais pas d'une panne du disque. Un disque externe est conseillé.",
                                        "sub", wrap=True))
            elif not C.liens_durs_possibles(C.dossier_capsule(dest)) if os.path.isdir(C.dossier_capsule(dest)) \
                    else False:
                pg.body.addWidget(label("⚠️ Ce disque est formaté en FAT/exFAT : chaque sauvegarde sera "
                                        "complète et prendra beaucoup de place. Le format ext4 est conseillé.",
                                        "sub", wrap=True))

        # Instantanés
        if snaps:
            pg.body.addWidget(label("RETROUVER UN FICHIER", "section"))
            lcard = Card()
            for t, chemin in snaps[:30]:
                bx = QWidget()
                h = QHBoxLayout(bx)
                h.setContentsMargins(0, 0, 0, 0)
                h.addWidget(button("Parcourir", "link", lambda _=False, c=chemin: spawn(["xdg-open", c])))
                h.addWidget(button("Tout récupérer…", None, lambda _=False, c=chemin, t=t: self._capsule_restaurer(c, t)))
                lcard.add(SettingRow(C.libelle(t), None, bx))
            pg.body.addWidget(lcard)
            pg.body.addWidget(label("« Parcourir » ouvre la sauvegarde comme un dossier normal : copiez-en ce dont "
                                    "vous avez besoin. « Tout récupérer » la copie dans un nouveau dossier, sans "
                                    "toucher à vos fichiers actuels.", "sub", wrap=True))
        return finish(pg)

    def _capsule_destination(self, chemin):
        from . import capsule as C
        C.ecrire_conf(destination=chemin, active="true")
        spawn(["systemctl", "--user", "enable", "--now", "nounoursos-capsule.timer"])
        self.open_page("capsule")

    def _capsule_maintenant(self):
        from . import capsule as C

        class Fil(QThread):
            avance = pyqtSignal(int)
            fini = pyqtSignal(bool, str)

            def run(self):
                ok, msg = C.sauvegarder(progression=self.avance.emit, journal=lambda m: None)
                self.fini.emit(ok, msg)
        self.caps_btn.setEnabled(False)
        self.caps_prog.setValue(0)
        self.caps_prog.show()
        self.caps_msg.setText("Sauvegarde en cours… vous pouvez continuer à travailler.")
        self._caps_fil = Fil()
        self._caps_fil.avance.connect(self.caps_prog.setValue)
        self._caps_fil.fini.connect(lambda ok, msg: (self.caps_prog.hide(), self.caps_btn.setEnabled(True),
                                                      self.caps_msg.setText(msg), ok and self.open_page("capsule")))
        self._caps_fil.start()

    def _capsule_restaurer(self, chemin, t):
        from . import capsule as C
        cible = os.path.join(os.path.expanduser("~"), time.strftime("Récupéré du %d-%m-%Y à %Hh%M", time.localtime(t)))
        self.caps_msg.setText("Récupération en cours…")

        class Fil(QThread):
            fini = pyqtSignal(bool)

            def run(self):
                self.fini.emit(C.restaurer(chemin, cible))
        self._caps_rest = Fil()
        self._caps_rest.fini.connect(lambda ok: (self.caps_msg.setText(
            f"Fichiers récupérés dans « {os.path.basename(cible)} »." if ok else "La récupération a échoué."),
            ok and spawn(["xdg-open", cible])))
        self._caps_rest.start()

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
                  "Plusieurs façons de lancer vos logiciels Windows : directement avec la couche NT (Wine), "
                  "dans LiberNT, un système NT libre, ou dans un vrai Windows avec WinBoat.")
        self._section_nt(pg)
        self._section_libernt(pg)
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

    # LiberNT : système NT libre (image officielle, dans une fenêtre) -------------------
    def _section_libernt(self, pg):
        outil = shutil.which("nounoursos-libernt")
        if not (outil or DEMO):
            return
        from PyQt6.QtWidgets import QProgressBar
        info = {"pret": True, "version": "nt10.0-043", "taille": 2_900_000_000, "qemu": True, "kvm": True} \
            if DEMO else {}
        if not DEMO:
            try:
                info = json.loads(run([outil, "etat"], timeout=10) or "{}")
            except ValueError:
                info = {}
        pg.body.addWidget(label("LIBERNT : UN SYSTÈME NT LIBRE", "section"))
        pg.body.addWidget(label("LiberNT est un système d'exploitation libre compatible avec Windows, développé "
                                "par un projet indépendant à partir de ReactOS. Il s'ouvre ici dans une fenêtre, "
                                "sans licence Windows. Encore en développement : idéal pour essayer, pas pour "
                                "vos logiciels importants. S'il s'arrête sur un écran bleu au démarrage, il "
                                "redémarre tout seul : le deuxième essai passe souvent.", "sub", wrap=True))
        card = Card()
        if info.get("pret"):
            detail = f"Version {info.get('version') or 'inconnue'} · {info.get('taille', 0) / 2 ** 30:.1f} Go"
            if not info.get("kvm"):
                detail += " · sans accélération (lent)"
            etat = "Prêt à démarrer"
        else:
            detail = "Environ 1 Go à télécharger depuis les versions publiées par le projet LiberNT."
            etat = "Pas encore téléchargé"
        self.lnt_ligne = SettingRow(etat, detail, None, real_icon("", 30, key="windows"))
        card.add(self.lnt_ligne)
        pg.body.addWidget(card)
        row = QHBoxLayout()
        if info.get("pret"):
            row.addWidget(button("Démarrer LiberNT", "primary", lambda: spawn([outil or "true", "demarrer"])))
            row.addWidget(button("Mettre à jour l'image", None, lambda: self._libernt_telecharger(outil)))
            row.addWidget(button("Supprimer", None, lambda: (run([outil, "supprimer"]) if outil else None,
                                                             self.open_page("windows"))))
        else:
            self.lnt_btn = button("Télécharger LiberNT", "primary", lambda: self._libernt_telecharger(outil))
            row.addWidget(self.lnt_btn)
        row.addStretch()
        w = QWidget()
        w.setLayout(row)
        pg.body.addWidget(w)
        self.lnt_prog = QProgressBar()
        self.lnt_prog.setRange(0, 100)
        self.lnt_prog.hide()
        pg.body.addWidget(self.lnt_prog)
        self.lnt_msg = label("", "sub", wrap=True)
        pg.body.addWidget(self.lnt_msg)

    def _libernt_telecharger(self, outil):
        from PyQt6.QtCore import QProcess
        if DEMO or not outil:
            self.lnt_msg.setText("[démo] téléchargement")
            return
        self.lnt_prog.setValue(0)
        self.lnt_prog.show()
        self.lnt_msg.setText("Recherche de la dernière version de LiberNT…")
        proc = QProcess(self)
        self._lnt_proc = proc
        erreur = {"txt": ""}

        def lire():
            for line in bytes(proc.readAllStandardOutput()).decode(errors="ignore").splitlines():
                if line.startswith("progression:"):
                    self.lnt_prog.setValue(int(line.split(":")[1]))
                    self.lnt_msg.setText("Téléchargement de LiberNT…")
                elif line.startswith("etape:"):
                    self.lnt_prog.setRange(0, 0)
                    self.lnt_msg.setText(line.split(":", 1)[1])
                elif line.startswith("version:"):
                    self.lnt_msg.setText("Téléchargement de LiberNT " + line.split(":", 1)[1] + "…")
                elif line.startswith("erreur:"):
                    erreur["txt"] = line.split(":", 1)[1]

        def fini(code, _st):
            self.lnt_prog.hide()
            self.lnt_prog.setRange(0, 100)
            if code == 0:
                self.open_page("windows")
            else:
                self.lnt_msg.setText("Le téléchargement a échoué" + (f" : {erreur['txt']}" if erreur["txt"] else
                                                                      ". Vérifiez votre connexion."))
        proc.readyReadStandardOutput.connect(lire)
        proc.finished.connect(fini)
        proc.start(outil, ["telecharger"])

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
        ban = os.path.join(DATA, "banniere.png")
        if os.path.exists(ban):
            pm = QPixmap(ban)
            dpr = self.devicePixelRatioF() or 1
            pm = pm.scaledToWidth(int(600 * dpr), Qt.TransformationMode.SmoothTransformation)
            pm.setDevicePixelRatio(dpr)
            lg.setPixmap(pm)
        else:
            lg.setPixmap(logo_pixmap(120))
        top.addWidget(lg, 0, Qt.AlignmentFlag.AlignHCenter)
        top.addSpacing(8)
        edition = {"nt": "NounoursOS NT", "server": "NounoursOS Server"}.get(
            rel.get("NOUNOURSOS_EDITION", ""), "NounoursOS")
        top.addWidget(label(f"{edition} {rel.get('VERSION_ID', '')} « {rel.get('NOUNOURSOS_CODENAME', '')} »",
                            "h1", align=Qt.AlignmentFlag.AlignCenter))
        top.addWidget(label(f"Basé sur Debian {rel.get('DEBIAN_CODENAME', 'trixie').capitalize()} · "
                            f"noyau Linux {os.uname().release.split('-')[0]}",
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
