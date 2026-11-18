"""Mise à jour de NounoursOS — fenêtre façon macOS + service de notification."""
import json
import os
import sys
import time

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QProcess
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QProgressBar, QScrollArea, QFrame, QSystemTrayIcon, QMenu)

from . import (label, button, logo_pixmap, Card, colors, stylesheet, spawn, read_conf,
               HONEY, CACHE_DIR, DEMO, os_release)
from . import updates as U

NOTIFY_FILE = os.path.join(CACHE_DIR, "maj-notifie.json")
CHECK_EVERY_H = 4
RENOTIFY_AFTER_H = 24


class CheckThread(QThread):
    done = pyqtSignal(object)

    def run(self):
        self.done.emit(U.check())


def reboot():
    if DEMO:
        print("[demo] reboot")
        return
    spawn(["sh", "-c", "dbus-send --session --type=method_call --dest=org.kde.LogoutPrompt "
                       "/LogoutPrompt org.kde.LogoutPrompt.promptReboot || systemctl reboot"])


# ==========================================================================
# Fenêtre principale
# ==========================================================================
class UpdateWindow(QWidget):
    def __init__(self, initial=None, check_now=True):
        super().__init__()
        self.setWindowTitle("Mise à jour de NounoursOS")
        self.setWindowIcon(QIcon.fromTheme("nounoursos"))
        self.setObjectName("Page")
        self.setMinimumWidth(640)
        self.state = initial or U.load_state()
        self.proc = None
        self.offline = False

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 26, 28, 22)
        root.setSpacing(16)

        head = QHBoxLayout()
        head.setSpacing(20)
        self.logo = QLabel()
        self.logo.setPixmap(logo_pixmap(96))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignTop)
        head.addWidget(self.logo)
        col = QVBoxLayout()
        col.setSpacing(4)
        self.title = label("", "h1")
        self.subtitle = label("", "sub", wrap=True)
        self.more = button("Plus d'infos…", "link", self.toggle_details)
        self.more.setSizePolicy(self.more.sizePolicy().horizontalPolicy(),
                                self.more.sizePolicy().verticalPolicy())
        col.addWidget(self.title)
        col.addWidget(self.subtitle)
        row_more = QHBoxLayout()
        row_more.addWidget(self.more)
        row_more.addStretch()
        col.addLayout(row_more)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.hide()
        self.status = label("", "sub")
        self.status.hide()
        col.addWidget(self.progress)
        col.addWidget(self.status)
        col.addStretch()
        head.addLayout(col, 1)
        root.addLayout(head)

        # Nouveautés de la version (texte publié dans le dépôt)
        self.notes_card = Card(margins=(18, 14, 18, 14))
        self.notes = QLabel()
        self.notes.setTextFormat(Qt.TextFormat.MarkdownText)
        self.notes.setWordWrap(True)
        self.notes.setStyleSheet("font-size: 10pt;")
        self.notes_card.add(self.notes)
        self.notes_card.hide()
        root.addWidget(self.notes_card)

        # Détails (liste des paquets)
        self.details = QScrollArea()
        self.details.setWidgetResizable(True)
        self.details.setMinimumHeight(220)
        self.details.hide()
        root.addWidget(self.details)

        # Boutons
        self.buttons = QHBoxLayout()
        self.buttons.addStretch()
        self.b_later = button("Plus tard", None, self.close)
        self.b_check = button("Rechercher", None, self.check)
        self.b_offline = button("Redémarrer et mettre à jour", None, lambda: self.install(True))
        self.b_now = button("Mettre à jour maintenant", "primary", lambda: self.install(False))
        self.b_reboot = button("Redémarrer", "primary", reboot)
        for b in (self.b_later, self.b_check, self.b_offline, self.b_now, self.b_reboot):
            self.buttons.addWidget(b)
        root.addLayout(self.buttons)

        self.show_state()
        if check_now:
            QTimer.singleShot(200, self.check)

    def _shrink(self):
        """Ajuste la hauteur de la fenêtre au contenu visible (y compris en réduction)."""
        QTimer.singleShot(0, lambda: self.resize(self.width(), self.sizeHint().height()))

    # --- États -----------------------------------------------------------
    def _btns(self, *visible):
        for b in (self.b_later, self.b_check, self.b_offline, self.b_now, self.b_reboot):
            b.setVisible(b in visible)

    def show_checking(self):
        self.title.setText("Recherche de mises à jour…")
        self.subtitle.setText("Connexion aux serveurs NounoursOS et Debian.")
        self.more.hide()
        self.progress.setRange(0, 0)
        self.progress.show()
        self.status.hide()
        self._btns(self.b_later)

    def show_state(self):
        s = self.state
        self.progress.hide()
        self.progress.setRange(0, 100)
        self.status.hide()
        rel = os_release()
        if s.count:
            self.title.setText(s.headline() + (" est disponible" if s.new_release else ""))
            sub = s.summary()
            if s.new_release:
                sub = f"Nouvelle version de NounoursOS — {sub}"
            elif s.security_count:
                sub += "\nRecommandé : ces mises à jour corrigent des failles de sécurité."
            if s.needs_reboot:
                sub += "\nUn redémarrage sera nécessaire."
            self.subtitle.setText(sub)
            self.notes.setText(s.notes or "")
            self.notes_card.setVisible(bool(s.notes))
            self.more.show()
            self.build_details()
            self._btns(self.b_later, self.b_offline, self.b_now)
        else:
            self.title.setText("NounoursOS est à jour")
            when = time.strftime("%d/%m/%Y à %H:%M", time.localtime(s.checked_at)) if s.checked_at else "jamais"
            msg = (f"NounoursOS {rel.get('VERSION_ID', '')} « {rel.get('NOUNOURSOS_CODENAME', '')} »"
                   f" — dernière vérification : {when}")
            if s.error:
                msg = s.error
            self.subtitle.setText(msg)
            self.more.hide()
            self.details.hide()
            self.notes_card.hide()
            self._btns(self.b_check, self.b_later)
        self._shrink()

    def build_details(self):
        c = colors()
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 6, 0)
        lay.setSpacing(10)
        groups = [
            ("Système NounoursOS", [u for u in self.state.updates if u.nounoursos]),
            ("Sécurité", [u for u in self.state.updates if u.security and not u.nounoursos]),
            ("Système et applications", [u for u in self.state.updates if not u.security and not u.nounoursos]),
        ]
        for title, items in groups:
            if not items:
                continue
            lay.addWidget(label(title.upper(), "section"))
            card = Card()
            for u in items:
                w = QWidget()
                h = QHBoxLayout(w)
                h.setContentsMargins(14, 8, 14, 8)
                name = label(u.name)
                name.setStyleSheet("font-size: 10pt; font-weight: 600;")
                ver = label(f"{u.old}  →  {u.new}", "sub")
                v = QVBoxLayout()
                v.setSpacing(0)
                v.addWidget(name)
                v.addWidget(ver)
                h.addLayout(v, 1)
                h.addWidget(label(U.human_size(u.size) if u.size else "", "sub"))
                card.add(w)
            lay.addWidget(card)
        lay.addStretch()
        self.details.setWidget(box)

    def toggle_details(self):
        vis = not self.details.isVisible()
        self.details.setVisible(vis)
        self.more.setText("Masquer les détails" if vis else "Plus d'infos…")
        self._shrink()

    def _explain_error(self):
        txt = "\n".join(self.log[-60:])
        if "Could not get lock" in txt or "Impossible d'obtenir le verrou" in txt:
            return "Une autre installation est en cours. Patientez quelques minutes puis réessayez."
        if "Temporary failure resolving" in txt or "Could not resolve" in txt or "Failed to fetch" in txt:
            return "Les serveurs de mise à jour sont injoignables. Vérifiez votre connexion à Internet."
        if "No space left" in txt or "You don't have enough free space" in txt:
            return "Espace disque insuffisant. Libérez de la place puis réessayez."
        if "unmet dependencies" in txt or "dépendances non satisfaites" in txt:
            return "Un paquet ne peut pas être installé pour le moment (dépendances)."
        return "Une erreur s'est produite pendant l'installation. Le détail est ci-dessous."

    def _show_log(self):
        """Affiche les dernières lignes du journal (et les garde dans ~/.cache/nounoursos)."""
        lines = [l for l in self.log if not l.startswith(("dlstatus:", "pmstatus:"))]
        text = "\n".join(lines[-40:]) or "(aucun détail)"
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(os.path.join(CACHE_DIR, "maj-erreur.log"), "w") as f:
                f.write("\n".join(self.log))
        except OSError:
            pass
        box = QLabel(text)
        box.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.setStyleSheet("font-family: monospace; font-size: 8.5pt; color: #5A4F63;")
        box.setWordWrap(True)
        holder = QWidget()
        v = QVBoxLayout(holder)
        v.addWidget(label("Détails (journal complet : /var/log/nounoursos/maj.log)", "sub"))
        v.addWidget(box)
        v.addStretch()
        self.details.setWidget(holder)
        self.details.show()
        self.more.hide()
        self._shrink()

    # --- Actions -----------------------------------------------------------
    def check(self):
        self.show_checking()
        self.th = CheckThread()
        self.th.done.connect(self._checked)
        self.th.start()

    def _checked(self, s):
        self.state = s
        self.show_state()

    def install(self, offline):
        self.offline = offline
        self.details.hide()
        self.notes_card.hide()
        self.more.hide()
        self.title.setText("Préparation de la mise à jour…" if not offline
                           else "Téléchargement de la mise à jour…")
        self.subtitle.setText("Votre mot de passe peut être demandé. "
                              "Vous pouvez continuer à utiliser l'ordinateur.")
        self.progress.setValue(0)
        self.progress.show()
        self.status.setText("Préparation…")
        self.status.show()
        self._btns()
        self.log = []
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._output)
        self.proc.finished.connect(self._finished)
        cmd = U.install_command(offline)
        self.proc.start(cmd[0], cmd[1:])

    def _output(self):
        for line in bytes(self.proc.readAllStandardOutput()).decode(errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            self.log.append(line)
            # Progression APT : dlstatus = téléchargement (0-40 %), pmstatus = installation (40-100 %)
            parts = line.split(":", 3)
            if len(parts) == 4 and parts[0] in ("dlstatus", "pmstatus"):
                try:
                    pct = float(parts[2])
                except ValueError:
                    continue
                if parts[0] == "dlstatus":
                    self.progress.setValue(int(pct * 0.4))
                    self.status.setText("Téléchargement des mises à jour…")
                else:
                    self.progress.setValue(40 + int(pct * 0.6))
                    pkg = parts[1] if parts[1] not in ("dpkg-exec", "") else ""
                    self.status.setText(f"Installation… {pkg}".strip())
            elif line.startswith("Percentage:"):           # ancien format (pkcon)
                try:
                    self.progress.setValue(int(line.split()[-1]))
                except ValueError:
                    pass

    def _finished(self, code, _status):
        need_reboot = self.state.needs_reboot
        if code == 0:
            self.progress.setValue(100)
            if self.offline:
                self.title.setText("Prête à être installée")
                self.subtitle.setText("La mise à jour s'installera au prochain redémarrage. "
                                      "L'opération peut prendre quelques minutes.")
                self._btns(self.b_later, self.b_reboot)
                self.b_reboot.setText("Redémarrer maintenant")
            else:
                new = self.state.new_release
                self.title.setText(f"NounoursOS {new} est installé" if new else "Mise à jour terminée")
                self.state = U.UpdateSet(checked_at=time.time())
                U.save_state(self.state)
                if need_reboot:
                    self.subtitle.setText("Redémarrez pour terminer l'installation.")
                    self._btns(self.b_later, self.b_reboot)
                else:
                    self.subtitle.setText("Votre système est à jour.")
                    self._btns(self.b_later)
                    self.b_later.setText("Fermer")
            self.status.hide()
        else:
            self.progress.hide()
            self.status.hide()
            if code in (126, 127):
                self.title.setText("Mise à jour annulée")
                self.subtitle.setText("Le mot de passe administrateur n'a pas été donné.")
            else:
                self.title.setText("La mise à jour n'a pas pu se terminer")
                self.subtitle.setText(self._explain_error())
                self._show_log()
            self._btns(self.b_later, self.b_now)
        self._shrink()


# ==========================================================================
# Service en arrière-plan : icône + notifications
# ==========================================================================
def tray_pixmap(count):
    pm = logo_pixmap(64).copy()
    if count:
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor("#E5484D"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(36, 0, 28, 28)
        p.end()
    return pm


class Daemon:
    def __init__(self, app):
        self.app = app
        self.win = None
        self.state = U.load_state()
        self.tray = QSystemTrayIcon(QIcon(tray_pixmap(0)))
        self.tray.setToolTip("Mise à jour de NounoursOS")
        menu = QMenu()
        a_open = QAction("Ouvrir Mise à jour de NounoursOS", menu)
        a_open.triggered.connect(self.open)
        a_check = QAction("Rechercher maintenant", menu)
        a_check.triggered.connect(self.check)
        menu.addAction(a_open)
        menu.addAction(a_check)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda r: self.open() if r in (QSystemTrayIcon.ActivationReason.Trigger,
                                                                QSystemTrayIcon.ActivationReason.DoubleClick) else None)
        self.tray.messageClicked.connect(self.open)
        self.menu = menu

        delay = int(os.environ.get("NOUNOURSOS_MAJ_DELAY", "90"))
        QTimer.singleShot(delay * 1000, self.check)
        self.timer = QTimer()
        self.timer.timeout.connect(self.check)
        self.timer.start(CHECK_EVERY_H * 3600 * 1000)
        self.update_tray()

    def check(self):
        conf = read_conf("maj.conf", {"recherche_auto": "true"})
        if conf.get("recherche_auto", "true") != "true":
            return
        self.th = CheckThread()
        self.th.done.connect(self._checked)
        self.th.start()

    def _checked(self, s):
        self.state = s
        self.update_tray()
        if s.count:
            self.maybe_notify(s)

    def update_tray(self):
        n = self.state.count
        self.tray.setIcon(QIcon(tray_pixmap(n)))
        self.tray.setVisible(n > 0)
        if n:
            self.tray.setToolTip(f"{self.state.headline()} — {self.state.summary()}")

    def maybe_notify(self, s):
        try:
            with open(NOTIFY_FILE) as f:
                last = json.load(f)
        except Exception:
            last = {}
        sig = s.signature()
        if last.get("sig") == sig and time.time() - last.get("at", 0) < RENOTIFY_AFTER_H * 3600:
            return
        if s.new_release:
            title = f"NounoursOS {s.new_release} est disponible"
            body = "Une nouvelle version de NounoursOS est prête. Cliquez pour en savoir plus."
        else:
            title = "Mise à jour de NounoursOS disponible"
            body = s.summary() + (". Recommandée pour votre sécurité." if s.security_count else ".")
        self.tray.showMessage(title, body, QIcon(tray_pixmap(0)), 15000)
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(NOTIFY_FILE, "w") as f:
            json.dump({"sig": sig, "at": time.time()}, f)

    def open(self):
        if self.win is None or not self.win.isVisible():
            self.win = UpdateWindow(self.state, check_now=not self.state.count)
            self.win.destroyed.connect(lambda: setattr(self, "win", None))
        self.win.show()
        self.win.raise_()
        self.win.activateWindow()


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--check" in argv:
        s = U.check()
        print(s.headline() if s.count else "À jour", "-", s.summary() if s.count else "")
        return 0
    app = QApplication(sys.argv)
    app.setApplicationName("nounoursos-maj")
    app.setDesktopFileName("nounoursos-maj")
    app.setStyleSheet(stylesheet())
    if "--daemon" in argv:
        try:  # pas de service de mise à jour en session live
            with open("/proc/cmdline") as f:
                if "boot=live" in f.read().split() and not DEMO:
                    return 0
        except OSError:
            pass
        app.setQuitOnLastWindowClosed(False)
        d = Daemon(app)  # noqa: F841
        return app.exec()
    w = UpdateWindow()
    w.show()
    return app.exec()
