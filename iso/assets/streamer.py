#!/usr/bin/env python3
"""Kit streamer NounoursOS : écrans de live (1920×1080) et cadre de caméra.

Sortie : desktop/includes.chroot/usr/share/nounoursos/streamer/
Ne pas retoucher les PNG : modifier ce fichier puis le relancer.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from identite import (DESK, MIEL, MIEL_CLAIR, NUIT, CREME, SLOGAN, fond_svg, logo_groupe, marque, png,  # noqa: E402
                      texte)

SORTIE = os.path.join(DESK, "usr", "share", "nounoursos", "streamer")
W, H = 1920, 1080
CAM = (1440, 750, 420, 236)          # x, y, l, h de la caméra dans « En direct »


def ecran(titre, sous, graine, nuit=0.0):
    fond = fond_svg(W, H, graine=graine, ourson_visible=False, nuit=nuit)
    corps = fond[fond.index(">") + 1:fond.rindex("</svg>")]
    k = 230
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{corps}'
            f'{logo_groupe(W / 2 - k / 2, 250, k, "couleur")}'
            + texte(W / 2, 620, titre, 104, poids=800, extra='letter-spacing="-2"')
            + texte(W / 2, 700, sous, 40, CREME, poids=500)
            + f'<rect x="{W / 2 - 60}" y="760" width="120" height="6" rx="3" fill="{MIEL_CLAIR}"/>'
            + marque(70, H - 60, 34, ancre="start")
            + texte(W - 70, H - 60, SLOGAN, 26, CREME, poids=500, ancre="end", extra='opacity="0.8"')
            + "</svg>")


def cadre():
    x, y, w, h = CAM
    e = 8
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{MIEL_CLAIR}"/>'
            f'<stop offset="1" stop-color="{MIEL}"/></linearGradient>'
            f'<mask id="m"><rect width="{W}" height="{H}" fill="white"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="black"/></mask></defs>'
            f'<rect x="{x - e}" y="{y - e}" width="{w + 2 * e}" height="{h + 2 * e}" rx="{18 + e}" fill="url(#g)" '
            f'mask="url(#m)"/>'
            f'<rect x="{x}" y="{y + h + e + 10}" width="{w}" height="46" rx="12" fill="{NUIT}" opacity="0.88"/>'
            + texte(x + w / 2, y + h + e + 42, "EN DIRECT", 22, MIEL_CLAIR, poids=800, extra='letter-spacing="4"')
            + f'<circle cx="{x + w / 2 - 92}" cy="{y + h + e + 34}" r="7" fill="#E5484D"/>'
            + "</svg>")


def generer():
    png(ecran("Ça commence bientôt", "Installez-vous, on arrive !", 31), f"{SORTIE}/bientot.png", W, H)
    png(ecran("Petite pause", "On revient dans quelques minutes.", 47, nuit=0.12), f"{SORTIE}/pause.png", W, H)
    png(ecran("Merci d'avoir regardé !", "À très vite pour le prochain live.", 59, nuit=0.2),
        f"{SORTIE}/fin.png", W, H)
    png(cadre(), f"{SORTIE}/cadre-camera.png", W, H)
    print(f"Kit streamer : {SORTIE}")


if __name__ == "__main__":
    generer()
