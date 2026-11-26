"""Aperçu rapide NounoursOS : regarder un fichier sans ouvrir d'application.

Images (y compris animées), PDF, vidéos et musique, textes et code, dossiers ; pour le
reste, l'icône et les informations du fichier. Espace ou Échap pour fermer, ← et → pour
passer au fichier voisin du même dossier, Entrée pour l'ouvrir avec l'application habituelle.
"""
import mimetypes
import os
import subprocess
import sys
import tempfile
import time

from PyQt6.QtCore import Qt, QUrl, QSize, QMimeDatabase
from PyQt6.QtGui import QPixmap, QMovie, QIcon, QFontDatabase, QKeySequence, QShortcut, QImage
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget,
                             QPlainTextEdit, QScrollArea, QListWidget, QListWidgetItem, QPushButton, QSizePolicy)

from . import stylesheet, button, label, HONEY

TEXTE_MAX = 400_000
MIMES = QMimeDatabase()


def taille_humaine(n):
    for unite in ("octets", "Ko", "Mo", "Go", "To"):
        if n < 1024 or unite == "To":
            return f"{n:.0f} {unite}" if unite == "octets" else f"{n:.1f} {unite}".replace(".", ",")
        n /= 1024
    return ""


def genre(chemin):
    if os.path.isdir(chemin):
        return "dossier"
    mime = MIMES.mimeTypeForFile(chemin).name()
    if mime == "image/svg+xml" or mime.startswith("image/"):
        return "animation" if mime in ("image/gif", "image/webp") and QMovie(chemin).frameCount() > 1 else "image"
    if mime == "application/pdf":
        return "pdf"
    if mime.startswith(("video/", "audio/")):
        return "media"
    if mime.startswith("text/") or MIMES.mimeTypeForFile(chemin).inherits("text/plain") or mime in (
            "application/json", "application/x-shellscript", "application/xml", "application/javascript",
            "application/x-yaml", "application/toml", "application/x-desktop"):
        return "texte"
    return "autre"


class Apercu(QWidget):
    def __init__(self, chemin):
        super().__init__()
        self.setWindowTitle("Aperçu rapide")
        self.setWindowFlag(Qt.WindowType.Dialog)
        self.resize(920, 680)
        self.media = None
        self.page_pdf = 0
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 14)
        lay.setSpacing(8)

        tete = QHBoxLayout()
        self.titre = label("", "h2")
        self.titre.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.infos = label("", "sub")
        col = QVBoxLayout()
        col.setSpacing(0)
        col.addWidget(self.titre)
        col.addWidget(self.infos)
        tete.addLayout(col, 1)
        self.prec_pdf = button("‹", None, lambda: self.pdf_page(-1))
        self.suiv_pdf = button("›", None, lambda: self.pdf_page(1))
        tete.addWidget(self.prec_pdf)
        tete.addWidget(self.suiv_pdf)
        tete.addWidget(button("Ouvrir", "primary", self.ouvrir))
        tete.addWidget(button("Fermer", None, self.close))
        lay.addLayout(tete)

        self.pile = QStackedWidget()
        lay.addWidget(self.pile, 1)
        self.vue_image = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.vue_image.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.vue_texte = QPlainTextEdit(readOnly=True)
        self.vue_texte.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.vue_liste = QListWidget()
        self.vue_liste.setIconSize(QSize(28, 28))
        self.vue_autre = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.vue_media = QWidget()
        for w in (self.vue_image, self.vue_texte, self.vue_liste, self.vue_autre, self.vue_media):
            self.pile.addWidget(w)

        for touche, fonction in (("Space", self.close), ("Escape", self.close), ("Return", self.ouvrir),
                                 ("Right", lambda: self.voisin(1)), ("Left", lambda: self.voisin(-1)),
                                 ("Down", lambda: self.voisin(1)), ("Up", lambda: self.voisin(-1)),
                                 ("PgDown", lambda: self.pdf_page(1)), ("PgUp", lambda: self.pdf_page(-1))):
            QShortcut(QKeySequence(touche), self, fonction)
        self.charger(chemin)

    # --- Chargement -----------------------------------------------------------------
    def charger(self, chemin):
        self.arreter_media()
        self.chemin = os.path.abspath(chemin)
        self.genre = genre(self.chemin)
        st = os.stat(self.chemin)
        type_ = MIMES.mimeTypeForFile(self.chemin).comment() if self.genre != "dossier" else "Dossier"
        self.titre.setText(os.path.basename(self.chemin) or self.chemin)
        quand = time.strftime("%d/%m/%Y %H:%M", time.localtime(st.st_mtime))
        details = [type_, quand]
        if self.genre != "dossier":
            details.insert(1, taille_humaine(st.st_size))
        self.infos.setText(" · ".join(details))
        self.prec_pdf.setVisible(self.genre == "pdf")
        self.suiv_pdf.setVisible(self.genre == "pdf")
        getattr(self, "montrer_" + self.genre)()
        self.setWindowTitle(f"Aperçu rapide — {os.path.basename(self.chemin)}")

    def montrer_image(self):
        self._pix = QPixmap(self.chemin)
        if self._pix.isNull():
            return self.montrer_autre()
        self.pile.setCurrentWidget(self.vue_image)
        w, h = self._pix.width(), self._pix.height()
        self.infos.setText(self.infos.text() + f" · {w} × {h}")
        self.ajuster_image()

    def montrer_animation(self):
        self.pile.setCurrentWidget(self.vue_image)
        self._pix = None
        self._film = QMovie(self.chemin)
        self.vue_image.setMovie(self._film)
        self._film.start()

    def ajuster_image(self):
        if getattr(self, "_pix", None) is not None and not self._pix.isNull() and self.genre == "image":
            dpr = self.devicePixelRatioF()
            cible = self.vue_image.size() * dpr
            pm = self._pix.scaled(cible, Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation) \
                if self._pix.width() > cible.width() or self._pix.height() > cible.height() else self._pix
            pm.setDevicePixelRatio(dpr)
            self.vue_image.setPixmap(pm)

    def montrer_pdf(self):
        self.page_pdf = 0
        self._pdf = None
        try:
            from PyQt6.QtPdf import QPdfDocument
            self._pdf = QPdfDocument(self)
            self._pdf.load(self.chemin)
            self.nb_pages = self._pdf.pageCount()
        except ImportError:
            out = subprocess.run(["pdfinfo", self.chemin], capture_output=True, text=True).stdout
            self.nb_pages = next((int(l.split()[-1]) for l in out.splitlines() if l.startswith("Pages:")), 1)
        self.pile.setCurrentWidget(self.vue_image)
        self.genre = "pdf"
        self.rendre_pdf()

    def rendre_pdf(self):
        taille = self.vue_image.size() * self.devicePixelRatioF()
        if self._pdf is not None:
            pt = self._pdf.pagePointSize(self.page_pdf)
            k = min(taille.width() / max(pt.width(), 1), taille.height() / max(pt.height(), 1))
            img = self._pdf.render(self.page_pdf, QSize(int(pt.width() * k), int(pt.height() * k)))
        else:
            sortie = os.path.join(tempfile.gettempdir(), f"nounoursos-apercu-{os.getpid()}")
            subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", str(self.page_pdf + 1), "-l",
                            str(self.page_pdf + 1), "-singlefile", self.chemin, sortie], capture_output=True)
            img = QImage(sortie + ".png").scaled(taille, Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation)
        pm = QPixmap.fromImage(img)
        pm.setDevicePixelRatio(self.devicePixelRatioF())
        self.vue_image.setPixmap(pm)
        base = self.infos.text().split(" · page")[0]
        self.infos.setText(f"{base} · page {self.page_pdf + 1} sur {self.nb_pages}")

    def pdf_page(self, delta):
        if self.genre == "pdf":
            self.page_pdf = max(0, min(self.nb_pages - 1, self.page_pdf + delta))
            self.rendre_pdf()

    def montrer_texte(self):
        with open(self.chemin, "rb") as f:
            brut = f.read(TEXTE_MAX)
        texte = brut.decode("utf-8", errors="replace")
        if os.path.getsize(self.chemin) > TEXTE_MAX:
            texte += "\n\n… (suite non affichée)"
        self.vue_texte.setPlainText(texte)
        self.pile.setCurrentWidget(self.vue_texte)

    def montrer_dossier(self):
        self.vue_liste.clear()
        try:
            noms = sorted(os.listdir(self.chemin), key=lambda n: (not os.path.isdir(os.path.join(self.chemin, n)),
                                                                   n.lower()))
        except OSError:
            noms = []
        visibles = [n for n in noms if not n.startswith(".")]
        for n in visibles[:500]:
            p = os.path.join(self.chemin, n)
            ic = QIcon.fromTheme("folder" if os.path.isdir(p) else MIMES.mimeTypeForFile(p).iconName(),
                                 QIcon.fromTheme("text-x-generic"))
            QListWidgetItem(ic, n, self.vue_liste)
        self.infos.setText(self.infos.text() + f" · {len(visibles)} élément" + ("s" if len(visibles) > 1 else ""))
        self.pile.setCurrentWidget(self.vue_liste)

    def montrer_media(self):
        try:
            from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
            from PyQt6.QtMultimediaWidgets import QVideoWidget
        except ImportError:
            return self.montrer_autre()
        if self.vue_media.layout() is None:
            v = QVBoxLayout(self.vue_media)
            v.setContentsMargins(0, 0, 0, 0)
            self.video = QVideoWidget()
            v.addWidget(self.video, 1)
            self.media_info = label("", "sub", align=Qt.AlignmentFlag.AlignCenter)
            v.addWidget(self.media_info)
        self.media = QMediaPlayer(self)
        self.sortie_audio = QAudioOutput(self)
        self.media.setAudioOutput(self.sortie_audio)
        self.media.setVideoOutput(self.video)
        self.media.setSource(QUrl.fromLocalFile(self.chemin))
        self.media.play()
        audio = MIMES.mimeTypeForFile(self.chemin).name().startswith("audio/")
        self.media_info.setText("♪ Lecture…  (Espace pour fermer)" if audio else "")
        self.pile.setCurrentWidget(self.vue_media)

    def montrer_autre(self):
        ic = QIcon.fromTheme(MIMES.mimeTypeForFile(self.chemin).iconName(), QIcon.fromTheme("unknown"))
        self.vue_autre.setPixmap(ic.pixmap(160, 160))
        self.pile.setCurrentWidget(self.vue_autre)

    # --- Actions --------------------------------------------------------------------
    def arreter_media(self):
        if self.media is not None:
            self.media.stop()
            self.media.deleteLater()
            self.media = None
        if getattr(self, "_film", None) is not None:
            self._film.stop()
            self._film = None
            self.vue_image.setMovie(None)

    def voisin(self, sens):
        dossier = os.path.dirname(self.chemin)
        try:
            noms = sorted((n for n in os.listdir(dossier) if not n.startswith(".")), key=str.lower)
        except OSError:
            return
        if os.path.basename(self.chemin) not in noms or len(noms) < 2:
            return
        i = (noms.index(os.path.basename(self.chemin)) + sens) % len(noms)
        self.charger(os.path.join(dossier, noms[i]))

    def ouvrir(self):
        subprocess.Popen(["xdg-open", self.chemin], start_new_session=True)
        self.close()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.genre == "image":
            self.ajuster_image()
        elif self.genre == "pdf":
            self.rendre_pdf()

    def closeEvent(self, e):
        self.arreter_media()
        super().closeEvent(e)


def main(argv=None):
    argv = argv or sys.argv
    app = QApplication(argv)
    app.setApplicationName("Aperçu rapide")
    app.setDesktopFileName("nounoursos-apercu")
    app.setStyleSheet(stylesheet())
    fichiers = [a for a in argv[1:] if not a.startswith("-")]
    if not fichiers or not os.path.exists(fichiers[0]):
        print("Usage : nounoursos-apercu FICHIER")
        return 2
    w = Apercu(fichiers[0])
    w.show()
    return app.exec()
