"""Écran de veille NounoursOS.

Plein écran, sur chaque écran :
  - écran principal : horloge géante, ourson en rotation 3D avec son état
    (Tout va bien / Erreur système / Surchauffe), ressources de la machine ;
  - écrans secondaires : journal système en direct + ressources.
Le journal vient de `journalctl -f` (rejoue l'historique s'il ne se passe rien).
Toute touche, clic ou mouvement de souris le ferme.

Options : --auto (lancé par l'inactivité : ne démarre pas si une vidéo ou un
jeu bloque la veille), --fenetre (aperçu dans une fenêtre).
Démo : NOUNOURSOS_VEILLE_DEMO=1 (ou =erreur, =chaud).
"""
import glob
import math
import os
import random
import shutil
import subprocess
import sys
import time
from collections import deque

from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, QProcess, QLocale, QDateTime
from PyQt6.QtGui import (QColor, QPainter, QLinearGradient, QRadialGradient, QFont, QPen,
                         QPainterPath, QGuiApplication, QTransform)
from PyQt6.QtWidgets import QApplication, QWidget

from . import logo_pixmap, read_conf, HONEY, HONEY_LIGHT

DEMO = os.environ.get("NOUNOURSOS_VEILLE_DEMO", "")
CREME = QColor(246, 236, 222)
CREME_DOUX = QColor(246, 236, 222, 150)
ROUGE = QColor("#FF6B6B")


# ==========================================================================
# Mesures système
# ==========================================================================
class Mesures:
    def __init__(self):
        self.cpu_prev = self._cpu_times()
        self.net_prev = (self._net_bytes(), time.time())
        self.cpu = 0.0
        self.coeurs = []
        self.ram = (0, 0)
        self.disque = (0, 0)
        self.temp = None
        self.down = self.up = 0.0
        self.charge = 0.0
        self.uptime = 0
        self.maj()

    @staticmethod
    def _cpu_times():
        out = {}
        try:
            with open("/proc/stat") as f:
                for line in f:
                    if line.startswith("cpu"):
                        p = line.split()
                        vals = list(map(int, p[1:9]))
                        out[p[0]] = (sum(vals) - vals[3] - vals[4], sum(vals))
        except OSError:
            pass
        return out

    @staticmethod
    def _net_bytes():
        rx = tx = 0
        try:
            with open("/proc/net/dev") as f:
                for line in f.readlines()[2:]:
                    name, data = line.split(":", 1)
                    if name.strip() == "lo":
                        continue
                    v = data.split()
                    rx += int(v[0])
                    tx += int(v[8])
        except OSError:
            pass
        return rx, tx

    @staticmethod
    def _temperature():
        best = None
        for path in glob.glob("/sys/class/thermal/thermal_zone*/temp") + \
                glob.glob("/sys/class/hwmon/hwmon*/temp1_input"):
            try:
                with open(path) as f:
                    t = int(f.read().strip()) / 1000
                if 0 < t < 130:
                    best = t if best is None else max(best, t)
            except (OSError, ValueError):
                continue
        return best

    def maj(self):
        if DEMO:
            t = time.time()
            self.cpu = 30 + 25 * math.sin(t / 3)
            self.coeurs = [max(2, min(99, 40 + 35 * math.sin(t / 2 + i))) for i in range(8)]
            self.ram = (6.2e9, 16e9)
            self.disque = (52e9, 128e9)
            self.temp = 91.0 if DEMO == "chaud" else 54 + 4 * math.sin(t / 5)
            self.down, self.up = 2.4e6 * (1 + math.sin(t)), 3.1e5
            self.charge, self.uptime = 0.82, 3 * 3600 + 1234
            return
        cur = self._cpu_times()
        coeurs = []
        for k, (busy, total) in cur.items():
            pb, pt = self.cpu_prev.get(k, (busy, total))
            pct = 100.0 * (busy - pb) / (total - pt) if total > pt else 0.0
            if k == "cpu":
                self.cpu = pct
            else:
                coeurs.append(pct)
        self.coeurs = coeurs
        self.cpu_prev = cur
        try:
            info = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    k, v = line.split(":", 1)
                    info[k] = int(v.split()[0]) * 1024
            self.ram = (info["MemTotal"] - info.get("MemAvailable", 0), info["MemTotal"])
        except Exception:
            pass
        du = shutil.disk_usage("/")
        self.disque = (du.used, du.total)
        self.temp = self._temperature()
        (rx, tx), now = self._net_bytes(), time.time()
        (prx, ptx), pnow = self.net_prev
        dt = max(0.001, now - pnow)
        self.down, self.up = max(0, rx - prx) / dt, max(0, tx - ptx) / dt
        self.net_prev = ((rx, tx), now)
        try:
            self.charge = os.getloadavg()[0]
            with open("/proc/uptime") as f:
                self.uptime = int(float(f.read().split()[0]))
        except OSError:
            pass


def taille(n):
    for u in ("o", "Ko", "Mo", "Go", "To"):
        if n < 1024 or u == "To":
            return (f"{n:.0f} {u}" if u in ("o", "Ko") else f"{n:.1f} {u}").replace(".", ",")
        n /= 1024


def debit(n):
    return taille(n) + "/s"


# ==========================================================================
# Journal système
# ==========================================================================
class Journal:
    """Dernières lignes du journal ; signale les erreurs récentes."""

    def __init__(self, parent):
        self.lignes = deque(maxlen=60)
        self.erreur_jusqua = 0.0
        self.dernier_neuf = time.time()
        self.historique = []
        self.proc = None
        if DEMO:
            self._demo()
            return
        self.historique = self._historique()
        for l in self.historique[-20:]:
            self.lignes.append((l, False))
        self.proc = QProcess(parent)
        self.proc.readyReadStandardOutput.connect(self._lire)
        self.proc.start("journalctl", ["-f", "-n", "0", "-o", "json-seq", "--output-fields=MESSAGE,PRIORITY,SYSLOG_IDENTIFIER,_COMM"])

    def _historique(self):
        try:
            out = subprocess.run(["journalctl", "-n", "200", "-o", "short", "--no-pager"],
                                 capture_output=True, text=True, timeout=5).stdout
            return [self._court(l) for l in out.splitlines() if l and not l.startswith("--")]
        except Exception:
            return []

    @staticmethod
    def _court(line):
        # « nov. 24 10:02:11 machine programme[123]: message » -> « 10:02:11 programme : message »
        p = line.split(None, 4)
        if len(p) >= 5:
            prog = p[4].split(":", 1)
            if len(prog) == 2:
                return f"{p[2]}  {prog[0].split('[')[0]} : {prog[1].strip()}"
        return line

    def _lire(self):
        import json
        data = bytes(self.proc.readAllStandardOutput()).decode(errors="ignore")
        for chunk in data.split("\x1e"):
            chunk = chunk.strip()
            if not chunk:
                continue
            try:
                d = json.loads(chunk)
            except ValueError:
                continue
            msg = d.get("MESSAGE")
            if isinstance(msg, list):
                continue
            prog = d.get("SYSLOG_IDENTIFIER") or d.get("_COMM") or "système"
            err = str(d.get("PRIORITY", "6")) in ("0", "1", "2", "3")
            self.lignes.append((f"{time.strftime('%H:%M:%S')}  {prog} : {msg}", err))
            self.dernier_neuf = time.time()
            if err:
                self.erreur_jusqua = time.time() + 20

    def tic(self):
        """S'il ne se passe rien, rejoue une ligne d'historique (comme un vieux terminal)."""
        if DEMO:
            if random.random() < 0.35:
                self.lignes.append(random.choice(self._demo_lignes))
            return
        if time.time() - self.dernier_neuf > 4 and self.historique:
            self.lignes.append((random.choice(self.historique), False))

    @property
    def en_erreur(self):
        return time.time() < self.erreur_jusqua

    def _demo(self):
        self._demo_lignes = [
            ("10:41:02  NetworkManager : connexion Wi-Fi « Freebox-NounoursCorp » active", False),
            ("10:41:05  systemd : Démarrage du service de mise à jour NounoursOS", False),
            ("10:41:07  nounoursos-maj : 3 mises à jour disponibles", False),
            ("10:41:12  kwin_wayland : écran HDMI-A-1 branché (2560×1440)", False),
            ("10:41:20  pipewire : nouvelle sortie audio « Casque Nounours »", False),
            ("10:41:31  docker : conteneur winboat démarré", False),
            ("10:41:44  plasmashell : widget Horloge NounoursOS chargé", False),
        ]
        for l in self._demo_lignes:
            self.lignes.append(l)
        if DEMO == "erreur":
            self.lignes.append(("10:41:50  kernel : usb 1-2: device descriptor read error", True))
            self.erreur_jusqua = time.time() + 3600


# ==========================================================================
# Dessin
# ==========================================================================
def fond(p, r):
    g = QLinearGradient(0, 0, r.width(), r.height())
    g.setColorAt(0, QColor("#15111F"))
    g.setColorAt(0.6, QColor("#241B33"))
    g.setColorAt(1, QColor("#3A2A2E"))
    p.fillRect(r, g)
    glow = QRadialGradient(QPointF(r.width() * 0.5, r.height() * 0.42), r.width() * 0.45)
    glow.setColorAt(0, QColor(243, 181, 98, 38))
    glow.setColorAt(1, QColor(243, 181, 98, 0))
    p.fillRect(r, glow)


def carte(p, rect, titre):
    path = QPainterPath()
    path.addRoundedRect(rect, 18, 18)
    p.fillPath(path, QColor(255, 255, 255, 14))
    p.setPen(QPen(QColor(255, 255, 255, 26), 1))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(path)
    f = QFont("Noto Sans", 10)
    f.setBold(True)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
    p.setFont(f)
    p.setPen(QColor(HONEY_LIGHT))
    p.drawText(QRectF(rect.x() + 22, rect.y() + 14, rect.width() - 44, 24),
               Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, titre)
    return QRectF(rect.x() + 22, rect.y() + 46, rect.width() - 44, rect.height() - 62)


def barre(p, x, y, w, frac, couleur=HONEY):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 30))
    p.drawRoundedRect(QRectF(x, y, w, 6), 3, 3)
    p.setBrush(QColor(couleur))
    p.drawRoundedRect(QRectF(x, y, max(6, w * max(0.0, min(1.0, frac))), 6), 3, 3)


class Veille(QWidget):
    def __init__(self, principal, mesures, journal, n_ecrans):
        super().__init__()
        self.principal = principal
        self.m = mesures
        self.j = journal
        self.n_ecrans = n_ecrans
        self.angle = 0.0
        self.logo = logo_pixmap(320)
        self.setWindowTitle("Écran de veille NounoursOS")
        self.setCursor(Qt.CursorShape.BlankCursor)
        self.setMouseTracking(True)
        self._souris = None
        self._debut = time.time()
        self.locale = QLocale(QLocale.Language.French, QLocale.Country.France)
        t = QTimer(self)
        t.timeout.connect(self._anim)
        t.start(33)

    def _anim(self):
        self.angle = (self.angle + 1.6) % 360
        self.update()

    # Sortie au moindre geste (sauf pendant la première seconde)
    def _quitter(self):
        if time.time() - self._debut > 1.0:
            QApplication.quit()

    def keyPressEvent(self, e):
        self._quitter()

    def mousePressEvent(self, e):
        self._quitter()

    def mouseMoveEvent(self, e):
        pos = e.position()
        if self._souris is None:
            self._souris = pos
        elif (pos - self._souris).manhattanLength() > 12:
            self._quitter()

    # ------------------------------------------------------------------
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = self.rect()
        fond(p, r)
        W, H = r.width(), r.height()
        if self.principal:
            self._horloge(p, W, H)
            self._ourson(p, QPointF(W * 0.5, H * 0.47), min(W, H) * 0.105)
            self._ressources(p, QRectF(W * 0.04, H * 0.71, W * 0.44, H * 0.25))
            self._coeurs(p, QRectF(W * 0.52, H * 0.71, W * 0.44, H * 0.25))
        else:
            self._journal(p, QRectF(W * 0.04, H * 0.05, W * 0.92, H * 0.60))
            self._ressources(p, QRectF(W * 0.04, H * 0.70, W * 0.92, H * 0.25))
        p.end()

    def _horloge(self, p, W, H):
        now = QDateTime.currentDateTime()
        f = QFont("Noto Sans", 10)
        f.setWeight(QFont.Weight.Light)
        f.setPixelSize(int(H * 0.15))
        p.setFont(f)
        p.setPen(CREME)
        p.drawText(QRectF(0, H * 0.03, W, H * 0.18), Qt.AlignmentFlag.AlignCenter,
                   now.toString("HH:mm"))
        f2 = QFont("Noto Sans", 10)
        f2.setPixelSize(int(H * 0.03))
        p.setFont(f2)
        p.setPen(CREME_DOUX)
        p.drawText(QRectF(0, H * 0.21, W, H * 0.05), Qt.AlignmentFlag.AlignCenter,
                   self.locale.toString(now.date(), "dddd d MMMM yyyy").capitalize())

    def _etat(self):
        if self.m.temp is not None and self.m.temp >= 88:
            return "SURCHAUFFE", ROUGE, f"{self.m.temp:.0f} °C"
        if self.j.en_erreur:
            return "ERREUR SYSTÈME", ROUGE, "voir le journal"
        return "TOUT VA BIEN", QColor("#7BD88F"), "NounoursOS veille sur vous"

    def _ourson(self, p, centre, rayon):
        """Ourson en rotation sur l'axe vertical (fausse 3D : largeur = cos(angle))."""
        etat, couleur, detail = self._etat()
        a = math.radians(self.angle)
        sx = math.cos(a)
        # ombre au sol
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 70))
        p.drawEllipse(QPointF(centre.x(), centre.y() + rayon * 1.05), rayon * 0.75 * max(0.35, abs(sx)), rayon * 0.12)
        # anneau d'état qui pulse
        pulse = 0.5 + 0.5 * math.sin(time.time() * (6 if couleur == ROUGE else 2))
        c = QColor(couleur)
        c.setAlpha(int(60 + 120 * pulse) if couleur == ROUGE else 70)
        p.setPen(QPen(c, 4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(centre, rayon * 1.25, rayon * 1.25)
        # logo déformé
        p.save()
        p.setTransform(QTransform().translate(centre.x(), centre.y()).scale(max(0.04, abs(sx)), 1))
        size = rayon * 2
        if sx < 0:      # face arrière : silhouette assombrie
            p.setOpacity(0.5)
        p.drawPixmap(QRectF(-size / 2, -size / 2, size, size), self.logo, QRectF(self.logo.rect()))
        p.restore()
        # texte d'état
        f = QFont("Noto Sans", 10)
        f.setBold(True)
        f.setPixelSize(int(max(16, rayon * 0.2)))
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        p.setFont(f)
        p.setPen(couleur)
        p.drawText(QRectF(centre.x() - 400, centre.y() + rayon * 1.32, 800, rayon * 0.22),
                   Qt.AlignmentFlag.AlignCenter, etat)
        f2 = QFont("Noto Sans", 10)
        f2.setPixelSize(int(max(13, rayon * 0.14)))
        p.setFont(f2)
        p.setPen(CREME_DOUX)
        p.drawText(QRectF(centre.x() - 400, centre.y() + rayon * 1.58, 800, rayon * 0.24),
                   Qt.AlignmentFlag.AlignCenter, detail)

    def _ressources(self, p, rect):
        zone = carte(p, rect, "RESSOURCES")
        m = self.m
        lignes = [
            ("Processeur", f"{m.cpu:.0f} %", m.cpu / 100),
            ("Mémoire", f"{taille(m.ram[0])} / {taille(m.ram[1])}", m.ram[0] / max(1, m.ram[1])),
            ("Disque", f"{taille(m.disque[0])} / {taille(m.disque[1])}", m.disque[0] / max(1, m.disque[1])),
        ]
        if m.temp is not None:
            lignes.append(("Température", f"{m.temp:.0f} °C", m.temp / 100))
        h = zone.height() / (len(lignes) + 1)
        f = QFont("Noto Sans", 10)
        f.setPixelSize(int(max(11, min(18, h * 0.38))))
        p.setFont(f)
        for i, (nom, val, frac) in enumerate(lignes):
            y = zone.y() + i * h
            p.setPen(CREME_DOUX)
            p.drawText(QRectF(zone.x(), y, zone.width() * 0.4, h * 0.6), Qt.AlignmentFlag.AlignLeft, nom)
            p.setPen(CREME)
            p.drawText(QRectF(zone.x(), y, zone.width(), h * 0.6), Qt.AlignmentFlag.AlignRight, val)
            chaud = nom == "Température" and m.temp >= 88
            barre(p, zone.x(), y + h * 0.62, zone.width(), frac, "#FF6B6B" if chaud else HONEY)
        y = zone.y() + len(lignes) * h
        heures, reste = divmod(m.uptime, 3600)
        p.setPen(CREME_DOUX)
        p.drawText(QRectF(zone.x(), y, zone.width(), h), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   f"↓ {debit(m.down)}   ↑ {debit(m.up)}   ·   charge {m.charge:.2f}   ·   allumé depuis {heures} h {reste // 60:02d}")

    def _coeurs(self, p, rect):
        if self.n_ecrans > 1 or not self.m.coeurs:
            self._journal(p, rect)
            return
        zone = carte(p, rect, f"CŒURS ({len(self.m.coeurs)})")
        n = len(self.m.coeurs)
        gap = 6
        w = (zone.width() - gap * (n - 1)) / n
        for i, v in enumerate(self.m.coeurs):
            x = zone.x() + i * (w + gap)
            hh = zone.height() * max(0.03, v / 100)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, 22))
            p.drawRoundedRect(QRectF(x, zone.y(), w, zone.height()), 5, 5)
            g = QLinearGradient(0, zone.bottom() - hh, 0, zone.bottom())
            g.setColorAt(0, QColor(HONEY_LIGHT))
            g.setColorAt(1, QColor(HONEY))
            p.setBrush(g)
            p.drawRoundedRect(QRectF(x, zone.bottom() - hh, w, hh), 5, 5)

    def _journal(self, p, rect):
        zone = carte(p, rect, "JOURNAL DU SYSTÈME")
        f = QFont("Noto Sans Mono", 10)
        f.setStyleHint(QFont.StyleHint.Monospace)
        f.setPixelSize(int(max(11, min(17, zone.height() / 14))))
        p.setFont(f)
        lh = f.pixelSize() * 1.55
        n = max(1, int(zone.height() / lh))
        lignes = list(self.j.lignes)[-n:]
        fm = p.fontMetrics()
        for i, (txt, err) in enumerate(lignes):
            c = QColor(ROUGE if err else CREME)
            c.setAlpha(int(70 + 185 * (i + 1) / len(lignes)))
            p.setPen(c)
            p.drawText(QRectF(zone.x(), zone.y() + i * lh, zone.width(), lh),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       fm.elidedText(txt, Qt.TextElideMode.ElideRight, int(zone.width())))


# ==========================================================================
def inhibee():
    """Une appli (vidéo, jeu, présentation) empêche-t-elle la veille ?"""
    try:
        out = subprocess.run(["gdbus", "call", "--session", "--dest", "org.freedesktop.PowerManagement",
                              "--object-path", "/org/freedesktop/PowerManagement/Inhibit",
                              "--method", "org.freedesktop.PowerManagement.Inhibit.HasInhibit"],
                             capture_output=True, text=True, timeout=3).stdout
        return "true" in out
    except Exception:
        return False


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--auto" in argv:
        conf = read_conf("veille.conf", {"active": "true"})
        if conf.get("active") != "true" or inhibee():
            return 0
    app = QApplication(sys.argv)
    app.setApplicationName("nounoursos-veille")
    app.setDesktopFileName("nounoursos-veille")
    mesures = Mesures()
    journal = Journal(app)
    ecrans = QGuiApplication.screens()
    if "--fenetre" in argv:
        ecrans = ecrans[:1]
    fenetres = []
    prim = QGuiApplication.primaryScreen()
    for ecran in ecrans:
        w = Veille(ecran == prim or len(ecrans) == 1, mesures, journal, len(ecrans))
        if "--fenetre" in argv:
            w.resize(1280, 720)
            w.show()
        else:
            w.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            w.setScreen(ecran)
            w.setGeometry(ecran.geometry())
            w.showFullScreen()
        fenetres.append(w)
    t = QTimer()
    t.timeout.connect(lambda: (mesures.maj(), journal.tic()))
    t.start(1000)
    return app.exec()
