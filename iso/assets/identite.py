#!/usr/bin/env python3
"""Identité visuelle NounoursOS — source unique.

L'ourson origami (facettes géométriques, miel sur prune nuit), le fond « Origami »
(champ de triangles) et toutes leurs déclinaisons : logo, icônes, GRUB, Plymouth,
installateur, menu de l'ISO, écran de connexion.

Usage : python3 iso/assets/identite.py   (rsvg-convert, Pillow et la police Inter requis)
"""
import math
import os
import random
import subprocess
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.dirname(ICI)
COMMON = os.path.join(ISO, "common", "includes.chroot")
DESK = os.path.join(ISO, "desktop", "includes.chroot")

# --- Palette ----------------------------------------------------------------------
NUIT = "#1B1329"        # prune nuit (fonds)
NUIT2 = "#2A1B3D"       # prune (yeux, nez, texte foncé)
AUBE = "#4B2E5C"        # violet d'aube
MIEL = "#E0954A"        # miel (couleur d'accent)
MIEL_CLAIR = "#F5B862"
CREME = "#FCE8CC"
SLOGAN = "Doux dehors, solide dedans."

# --- L'ourson origami ----------------------------------------------------------------
PTS = {
    "T": (256, 132), "A": (176, 140), "C1": (106, 196), "C": (82, 284),
    "J": (116, 372), "J2": (184, 424), "B": (256, 444),
    "M": (256, 262), "Mu": (256, 292), "Mt": (204, 318), "Ml": (196, 372), "Mb": (256, 416),
    "Y": (184, 256),
}
# (sommets, couleur côté gauche, couleur côté droit) : lumière en haut à gauche
FACETTES = [
    (("T", "A", "M"), "#F5B862", "#DA8A40"),
    (("A", "C1", "M"), "#EBA457", "#CF7D39"),
    (("C1", "C", "M"), "#DD8F48", "#BF6B2F"),
    (("C", "Mt", "M"), "#D88843", "#B5642B"),
    (("C", "J", "Ml"), "#CC7C3B", "#A85A26"),
    (("C", "Ml", "Mt"), "#D3833F", "#AF5F29"),
    (("J", "J2", "Ml"), "#BF6F33", "#9C5022"),
    (("J2", "B", "Mb"), "#B06530", "#8E471E"),
    (("J2", "Mb", "Ml"), "#B96B32", "#984D21"),
    (("M", "Mt", "Mu"), "#E59C52", "#C77736"),
    (("Mu", "Mt", "Ml"), CREME, "#F0CFA3"),
    (("Mu", "Ml", "Mb"), "#F7DDB8", "#E9C28F"),
]
OREILLE = ("#D08038", "#B5632B")
OREILLE_IN = ("#8A4322", "#76381C")


def _p(k, cote):
    x, y = PTS[k]
    return (512 - x, y) if cote == 1 and x != 256 else (x, y)


def _poly(pts, fill, extra=""):
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    # contour de la même couleur : supprime les liserés entre facettes
    return f'<polygon points="{pts}" fill="{fill}" stroke="{fill}" stroke-width="1.2" stroke-linejoin="round"{extra}/>'


def _ngon(cx, cy, r, n, rot):
    return [(cx + r * math.cos(rot + 2 * math.pi * i / n), cy + r * math.sin(rot + 2 * math.pi * i / n))
            for i in range(n)]


def ourson(mode="couleur"):
    """Formes de l'ourson (sans balise <svg>), dans un carré 512.

    mode : « couleur », « blanc » (facettes blanches, pour fonds sombres)
    ou « prune » (une seule couleur, pour fonds clairs / symbolique)."""
    out = []

    def teinte(c, cote, i):
        if mode == "couleur":
            return c
        if mode == "prune":
            return NUIT2
        # blanc : opacité selon la facette, pour garder le relief
        return f'#FFFFFF" fill-opacity="{0.96 - 0.06 * (i % 4) - 0.1 * cote:.2f}'

    for cote, s in ((0, 1), (1, -1)):
        cx = 256 - s * 116
        out.append(_poly(_ngon(cx, 128, 64, 6, math.pi / 6), teinte(OREILLE[cote], cote, 2)))
        if mode == "couleur":
            out.append(_poly(_ngon(cx + s * 6, 136, 34, 6, math.pi / 6), OREILLE_IN[cote]))
    for i, (pts, cl, cr) in enumerate(FACETTES):
        for cote, c in ((0, cl), (1, cr)):
            out.append(_poly([_p(k, cote) for k in pts], teinte(c, cote, i)))
    yeux = NUIT2 if mode != "prune" else "#FFFFFF"
    for cote in (0, 1):
        x, y = _p("Y", cote)
        out.append(_poly([(x, y - 17), (x + 12, y), (x, y + 17), (x - 12, y)], yeux))
    out.append(_poly([(222, 314), (290, 314), (256, 352)], yeux))
    if mode == "couleur":
        out.append(_poly([(234, 318), (252, 318), (244, 328)], "#4A3560"))
    return "".join(out).replace('" fill-opacity', '" fill-opacity').replace('stroke="#FFFFFF" fill-opacity', 'stroke="#FFFFFF" stroke-opacity')


def logo_svg(mode="couleur"):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="36 36 440 440">{ourson(mode)}</svg>\n'


def logo_groupe(x, y, taille, mode="couleur"):
    """L'ourson en <g>, placé dans un autre SVG (coin haut-gauche, taille en px)."""
    k = taille / 440
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.4f}) translate(-36 -36)">{ourson(mode)}</g>'


# --- Fond « Origami » : champ de triangles ---------------------------------------------
def _mix(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _rampe(stops, t):
    t = max(0.0, min(1.0, t))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return _mix(c0, c1, (t - t0) / (t1 - t0) if t1 > t0 else 0)
    return stops[-1][1]


def fond_svg(w=1920, h=1080, accent=MIEL, lueur=MIEL_CLAIR, graine=17, ourson_visible=True, nuit=0.0):
    """Triangles qui passent de la nuit (haut gauche) à la lueur miel (bas droite)."""
    rnd = random.Random(graine)
    cols, rows = 22, 13
    cw, rh = w / cols, h / rows
    pts = {}
    for j in range(rows + 1):
        for i in range(cols + 1):
            jx = 0 if i in (0, cols) else rnd.uniform(-0.38, 0.38) * cw
            jy = 0 if j in (0, rows) else rnd.uniform(-0.38, 0.38) * rh
            pts[i, j] = (i * cw + jx, j * rh + jy)
    stops = [(0.0, NUIT), (0.42, "#2B1C40"), (0.62, AUBE), (0.82, accent), (1.0, lueur)]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
           f'<rect width="{w}" height="{h}" fill="{NUIT}"/>']
    for j in range(rows):
        for i in range(cols):
            a, b, c, d = pts[i, j], pts[i + 1, j], pts[i + 1, j + 1], pts[i, j + 1]
            tris = [(a, b, c), (a, c, d)] if (i + j) % 2 else [(a, b, d), (b, c, d)]
            for tri in tris:
                cx = sum(p[0] for p in tri) / 3 / w
                cy = sum(p[1] for p in tri) / 3 / h
                # diagonale vers le bas à droite, avec une vague douce
                t = 0.62 * cx + 0.55 * cy - 0.12 + 0.06 * math.sin(cx * 7 + cy * 3)
                t += rnd.uniform(-0.035, 0.035) - nuit
                fill = _rampe(stops, t)
                pts_s = " ".join(f"{x:.1f},{y:.1f}" for x, y in tri)
                out.append(f'<polygon points="{pts_s}" fill="{fill}" stroke="{fill}" stroke-width="0.8"/>')
    # Lueur douce en bas à droite
    out.append(f'<defs><radialGradient id="l" cx="0.86" cy="0.92" r="0.55">'
               f'<stop offset="0" stop-color="{lueur}" stop-opacity="{0.45 * (1 - 2 * nuit):.2f}"/>'
               f'<stop offset="1" stop-color="{lueur}" stop-opacity="0"/></radialGradient></defs>'
               f'<rect width="{w}" height="{h}" fill="url(#l)"/>')
    if ourson_visible:
        k = h * 0.5
        out.append(f'<g opacity="0.10">{logo_groupe(w * 0.68 - k / 2, h * 0.30, k, "blanc")}</g>')
    out.append("</svg>")
    return "".join(out)


# --- Rendu --------------------------------------------------------------------------
def png(svg, chemin, w, h=None):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as f:
        f.write(svg)
    cmd = ["rsvg-convert", "-w", str(w)] + (["-h", str(h)] if h else []) + [f.name, "-o", chemin]
    subprocess.run(cmd, check=True)
    os.unlink(f.name)


def ecrire(chemin, texte):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte)


def texte(x, y, txt, taille, couleur="#FFFFFF", poids=600, ancre="middle", famille="Inter Display", extra=""):
    txt = txt.replace("&", "&amp;")
    return (f'<text x="{x}" y="{y}" font-family="{famille}, Inter, sans-serif" font-size="{taille}" '
            f'font-weight="{poids}" fill="{couleur}" text-anchor="{ancre}" {extra}>{txt}</text>')


def marque(x, y, taille, couleur="#FFFFFF", ancre="middle"):
    """Mot-symbole : « Nounours » + « OS » en miel."""
    return (f'<text x="{x}" y="{y}" font-family="Inter Display, Inter, sans-serif" font-size="{taille}" '
            f'font-weight="700" letter-spacing="{-taille * 0.02:.1f}" fill="{couleur}" text-anchor="{ancre}">'
            f'Nounours<tspan fill="{MIEL_CLAIR}" font-weight="800">OS</tspan></text>')


def generer():
    # Logo et icônes
    for mode, nom in (("couleur", "logo.svg"), ("blanc", "logo-white.svg"), ("prune", "logo-prune.svg")):
        ecrire(os.path.join(ICI, nom), logo_svg(mode))
    ecrire(os.path.join(COMMON, "usr/share/nounoursos/logo.svg"), logo_svg())
    ecrire(os.path.join(COMMON, "usr/share/icons/hicolor/scalable/apps/nounoursos.svg"), logo_svg())
    ecrire(os.path.join(COMMON, "usr/share/icons/hicolor/symbolic/apps/nounoursos-symbolic.svg"),
           logo_svg("prune"))
    for s in (16, 22, 24, 32, 48, 64, 128, 256, 512):
        png(logo_svg(), os.path.join(COMMON, f"usr/share/icons/hicolor/{s}x{s}/apps/nounoursos.png"), s)
    png(logo_svg(), os.path.join(COMMON, "usr/share/nounoursos/logo-256.png"), 256)

    # Fond d'écran Origami (+ capture)
    fond = fond_svg()
    ecrire(os.path.join(ICI, "wallpaper.svg"), fond)
    wp = os.path.join(DESK, "usr/share/wallpapers/NounoursOS/contents")
    for w, h in ((1920, 1080), (2560, 1440), (3840, 2160)):
        png(fond, os.path.join(wp, f"images/{w}x{h}.png"), w, h)
    png(fond, os.path.join(wp, "screenshot.png"), 400, 225)

    # GRUB (menu de démarrage du système installé)
    grub_fond = fond_svg(ourson_visible=False, graine=23)
    png(grub_fond, os.path.join(DESK, "usr/share/grub/themes/nounoursos/background.png"), 1920, 1080)
    png(grub_fond, os.path.join(COMMON, "usr/share/nounoursos/grub-background.png"), 1920, 1080)
    png(logo_svg(), os.path.join(DESK, "usr/share/grub/themes/nounoursos/logo.png"), 128)

    # Plymouth : ourson + mot-symbole
    ply = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 300">'
           + logo_groupe(130, 10, 160) + marque(210, 236, 46) + "</svg>")
    png(ply, os.path.join(DESK, "usr/share/nounoursos/plymouth/watermark.png"), 420, 300)

    # Bannière (Paramètres › À propos, assistant de bienvenue)
    f = fond_svg(1200, 400, ourson_visible=False, graine=12, nuit=0.05)
    ban = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400">'
           f'<clipPath id="c"><rect width="1200" height="400" rx="36"/></clipPath>'
           f'<g clip-path="url(#c)">{f[f.index(">") + 1:-6]}</g>'
           + logo_groupe(96, 70, 260) + marque(400, 200, 92, ancre="start")
           + texte(404, 262, SLOGAN, 32, "#F3E6F7", 400, "start", "Inter") + "</svg>")
    png(ban, os.path.join(COMMON, "usr/share/nounoursos/banniere.png"), 1200, 400)

    # Installateur (Calamares)
    cal = os.path.join(DESK, "etc/calamares/branding/nounoursos")
    png(logo_svg(), os.path.join(cal, "logo.png"), 128)
    png(logo_svg(), os.path.join(cal, "icon.png"), 64)
    bienvenue = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 300">'
                 f'<clipPath id="c"><rect width="720" height="300" rx="22"/></clipPath>'
                 f'<g clip-path="url(#c)">{fond_svg(720, 300, ourson_visible=False, graine=5)[fond_svg(720, 300, ourson_visible=False, graine=5).index(">") + 1:-6]}</g>'
                 + logo_groupe(48, 58, 184) + marque(262, 150, 58, ancre="start")
                 + texte(264, 196, SLOGAN, 22, "#F3E6F7", 400, "start", "Inter") + "</svg>")
    png(bienvenue, os.path.join(cal, "welcome.png"), 720, 300)
    diapos = [
        ("Bienvenue dans NounoursOS", "Le bureau KDE Plasma, en Classique ou façon Mac,", "avec des Paramètres où tout est rangé."),
        ("Vos logiciels Windows", "WinBoat et la couche NT ouvrent les .exe", "d'un double-clic, dans des fenêtres NounoursOS."),
        ("Toujours à jour, sans y penser", "Les nouvelles versions arrivent comme sur un Mac,", "et la Capsule temporelle garde vos fichiers à l'abri."),
    ]
    for n, (titre, l1, l2) in enumerate(diapos, 1):
        f = fond_svg(800, 440, ourson_visible=False, graine=40 + n, nuit=0.16)
        corps = f[f.index(">") + 1:-6]
        d = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 440">{corps}'
             + logo_groupe(352, 70, 96)
             + texte(400, 236, titre, 38, "#FFFFFF", 700)
             + texte(400, 286, l1, 21, "#EADCF2", 400, famille="Inter")
             + texte(400, 316, l2, 21, "#EADCF2", 400, famille="Inter") + "</svg>")
        png(d, os.path.join(cal, f"slide{n}.png"), 800, 440)

    # Menu de démarrage de l'ISO (live-build le convertit pour syslinux et GRUB).
    # Logo et nom intégrés en image : la machine de build n'a pas la police Inter.
    import base64
    entete = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 170">'
              + logo_groupe(100, 0, 100) + marque(150, 150, 40) + "</svg>")
    tmp = os.path.join(tempfile.gettempdir(), "nounoursos-entete.png")
    png(entete, tmp, 600, 340)
    with open(tmp, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    f = fond_svg(640, 480, ourson_visible=False, graine=9, nuit=0.1)
    splash = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
              f'width="640" height="480" viewBox="0 0 640 480">{f[f.index(">") + 1:-6]}'
              f'<image x="170" y="34" width="300" height="170" xlink:href="data:image/png;base64,{b64}"/>'
              + texte(320, 226, "@VERSION_NOUNOURSOS@", 15, "#E7D6F0", 500, famille="DejaVu Sans")
              + texte(320, 462, SLOGAN, 12, "#CDB8DA", 400, famille="DejaVu Sans") + "</svg>\n")
    ecrire(os.path.join(ISO, "bootloaders", "splash.svg"), splash)

    # Écran de connexion (SDDM)
    sddm = os.path.join(DESK, "usr/share/sddm/themes/nounoursos")
    png(fond_svg(graine=31), os.path.join(sddm, "fond.png"), 1920, 1080)
    png(logo_svg(), os.path.join(sddm, "logo.png"), 256)
    png(fond_svg(ourson_visible=False, graine=31), os.path.join(sddm, "preview.png"), 640, 360)
    print("Identité NounoursOS générée.")


if __name__ == "__main__":
    generer()
