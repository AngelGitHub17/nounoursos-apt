#!/usr/bin/env python3
"""Curseur NounoursOS : flèche prune à liseré blanc, touches de miel, sablier animé.

Génère le thème Xcursor /usr/share/icons/NounoursOS (toutes les tailles usuelles et
les alias attendus par Qt, GTK, Firefox…). L'encodeur Xcursor est écrit ici : pas
besoin de xcursorgen.
Usage : python3 iso/assets/curseur.py   (rsvg-convert et Pillow requis)
"""
import io
import math
import os
import struct
import subprocess
import tempfile

from PIL import Image

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "desktop", "includes.chroot", "usr", "share", "icons", "NounoursOS")
TAILLES = (24, 32, 48, 64, 96)        # tailles nominales (la grille de dessin fait 32 unités)
PRUNE, MIEL, MIEL_CLAIR, BLANC = "#2A1B3D", "#D98A3F", "#F5B862", "#FFFFFF"
CONTOUR = f'stroke="{BLANC}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"'
OMBRE = ('<defs><filter id="o" x="-30%" y="-30%" width="160%" height="160%">'
         '<feDropShadow dx="0" dy="0.8" stdDeviation="0.9" flood-color="#000" flood-opacity="0.45"/></filter></defs>')

FLECHE = (f'<path d="M5.5 3.5 L5.5 24.5 L10.6 19.6 L14.2 27.6 L17.7 26.1 L14.2 18.3 L21.3 18.3 Z" '
          f'fill="{PRUNE}" {CONTOUR}/>'
          f'<path d="M7.4 8.4 L7.4 19.3 L10.9 15.9 Z" fill="{MIEL_CLAIR}" opacity="0.9"/>')


def svg(corps):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">{OMBRE}<g filter="url(#o)">{corps}</g></svg>'


def main_ouverte(doigt=True):
    """Main (lien) : index tendu."""
    if doigt:
        d = ("M12.2 4.2c1.2 0 2 .9 2 2v7.6l.2-.1c.9-.6 2.2-.3 2.7.6c.9-.5 2.1-.2 2.6.7c.9-.4 2-.1 2.5.8"
             "l.2.4c.6 1.1.9 2.4.9 3.7v2.9c0 3.8-3.1 6.9-6.9 6.9h-1.6c-2.2 0-4.3-1.1-5.6-2.9l-4-5.6"
             "c-.7-1-.5-2.3.5-3c.9-.6 2.1-.5 2.8.3l1.6 1.8V6.2c0-1.1.9-2 2.1-2z")
    else:
        d = ("M8.6 10.8c0-1.1.9-1.9 2-1.9s2 .8 2 1.9V9.2c0-1.1.9-2 2-2s2 .9 2 2v.4c.1-1 .9-1.7 1.9-1.7"
             "c1.1 0 2 .9 2 2v.6c.2-.9 1-1.5 1.9-1.5c1.1 0 1.9.9 1.9 1.9v8.4c0 4.2-3.4 7.6-7.6 7.6h-1.5"
             "c-2.4 0-4.6-1.2-6-3.2l-2.6-3.9c-.6-.9-.4-2.1.5-2.7c.9-.6 2-.4 2.6.4l.9 1.2z")
    return f'<path d="{d}" fill="{BLANC}" stroke="{PRUNE}" stroke-width="1.5" stroke-linejoin="round"/>'


def anneau(frame, n, cx=16, cy=16, r=8.5, ep=3.4, fond=True):
    """Anneau de chargement : arc miel qui tourne sur un rond prune."""
    a0 = 2 * math.pi * frame / n - math.pi / 2
    a1 = a0 + math.pi * 1.25
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    base = (f'<circle cx="{cx}" cy="{cy}" r="{r + ep / 2 + 1.3}" fill="{BLANC}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{PRUNE}" stroke-width="{ep}"/>') if fond else ""
    return base + (f'<path d="M{x0:.2f} {y0:.2f} A{r} {r} 0 1 1 {x1:.2f} {y1:.2f}" fill="none" '
                   f'stroke="{MIEL_CLAIR}" stroke-width="{ep}" stroke-linecap="round"/>')


def double_fleche(angle):
    corps = (f'<g transform="rotate({angle} 16 16)">'
             f'<path d="M16 3.5 L22 10 L18.2 10 L18.2 22 L22 22 L16 28.5 L10 22 L13.8 22 L13.8 10 L10 10 Z" '
             f'fill="{PRUNE}" {CONTOUR}/></g>')
    return corps


def croix_deplacer():
    bras = ""
    for a in (0, 90, 180, 270):
        bras += (f'<g transform="rotate({a} 16 16)"><path d="M16 2.8 L20.6 7.8 L17.6 7.8 L17.6 14.4 '
                 f'L14.4 14.4 L14.4 7.8 L11.4 7.8 Z" fill="{PRUNE}" {CONTOUR}/></g>')
    return bras + f'<circle cx="16" cy="16" r="2.6" fill="{MIEL_CLAIR}" stroke="{PRUNE}" stroke-width="1.2"/>'


def badge(symbole_svg):
    """Petit rond en bas à droite de la flèche (aide, copie, lien, interdit…)."""
    return (FLECHE + f'<circle cx="23.5" cy="23.5" r="6.4" fill="{MIEL}" stroke="{BLANC}" stroke-width="1.4"/>'
            + symbole_svg)


FORMES = {
    # nom : (svg ou liste d'images animées, point chaud (x, y) sur la grille 32, délai ms)
    "default": (svg(FLECHE), (5.5, 3.5)),
    "pointer": (svg(main_ouverte()), (12.2, 4.4)),
    "grab": (svg(main_ouverte(False)), (16, 14)),
    "grabbing": (svg(main_ouverte(False).replace(BLANC, "#F3E6D8")), (16, 14)),
    "text": (svg(f'<path d="M11 5h3.4c.7 0 1.2.3 1.6.8c.4-.5.9-.8 1.6-.8H21M11 27h3.4c.7 0 1.2-.3 1.6-.8'
                 f'c.4.5.9.8 1.6.8H21M16 6v20M13.2 16h5.6" fill="none" stroke="{BLANC}" stroke-width="4" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>'
                 f'<path d="M11 5h3.4c.7 0 1.2.3 1.6.8c.4-.5.9-.8 1.6-.8H21M11 27h3.4c.7 0 1.2-.3 1.6-.8'
                 f'c.4.5.9.8 1.6.8H21M16 6v20M13.2 16h5.6" fill="none" stroke="{PRUNE}" stroke-width="1.7" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>'), (16, 16)),
    "crosshair": (svg(f'<path d="M16 4v9M16 19v9M4 16h9M19 16h9" stroke="{BLANC}" stroke-width="4.2" '
                      f'stroke-linecap="round"/><path d="M16 4v9M16 19v9M4 16h9M19 16h9" stroke="{PRUNE}" '
                      f'stroke-width="1.8" stroke-linecap="round"/><circle cx="16" cy="16" r="1.4" '
                      f'fill="{MIEL}"/>'), (16, 16)),
    "not-allowed": (svg(badge(f'<path d="M20.4 26.6l6.2-6.2" stroke="{BLANC}" stroke-width="2" '
                              f'stroke-linecap="round"/><circle cx="23.5" cy="23.5" r="3.6" fill="none" '
                              f'stroke="{BLANC}" stroke-width="1.8"/>').replace(MIEL, "#D9534F", 1)), (5.5, 3.5)),
    "help": (svg(badge(f'<path d="M21.6 21.7a2 2 0 1 1 2.9 1.8c-.6.3-1 .7-1 1.3v.4" fill="none" '
                       f'stroke="{BLANC}" stroke-width="1.7" stroke-linecap="round"/>'
                       f'<circle cx="23.5" cy="27.1" r="1" fill="{BLANC}"/>')), (5.5, 3.5)),
    "copy": (svg(badge(f'<path d="M23.5 20.4v6.2M20.4 23.5h6.2" stroke="{BLANC}" stroke-width="2" '
                       f'stroke-linecap="round"/>')), (5.5, 3.5)),
    "alias": (svg(badge(f'<path d="M21 26l5-5M22.2 21h3.8v3.8" fill="none" stroke="{BLANC}" stroke-width="1.8" '
                        f'stroke-linecap="round" stroke-linejoin="round"/>')), (5.5, 3.5)),
    "context-menu": (svg(badge(f'<path d="M20.6 21.2h5.8M20.6 23.5h5.8M20.6 25.8h5.8" stroke="{BLANC}" '
                               f'stroke-width="1.5" stroke-linecap="round"/>')), (5.5, 3.5)),
    "move": (svg(croix_deplacer()), (16, 16)),
    "ns-resize": (svg(double_fleche(0)), (16, 16)),
    "ew-resize": (svg(double_fleche(90)), (16, 16)),
    "nesw-resize": (svg(double_fleche(45)), (16, 16)),
    "nwse-resize": (svg(double_fleche(-45)), (16, 16)),
    "wait": ([svg(anneau(i, 12)) for i in range(12)], (16, 16), 60),
    "progress": ([svg(FLECHE + f'<g transform="translate(13.5 13.5) scale(0.55)">{anneau(i, 12)}</g>')
                  for i in range(12)], (5.5, 3.5), 60),
    "cell": (svg(f'<path d="M16 6v20M6 16h20" stroke="{BLANC}" stroke-width="6.5" stroke-linecap="round"/>'
                 f'<path d="M16 6v20M6 16h20" stroke="{PRUNE}" stroke-width="3" stroke-linecap="round"/>'),
             (16, 16)),
    "zoom-in": (svg(f'<circle cx="13.5" cy="13.5" r="8" fill="{BLANC}" stroke="{PRUNE}" stroke-width="2.2"/>'
                    f'<path d="M19.6 19.6l7 7" stroke="{PRUNE}" stroke-width="3.4" stroke-linecap="round"/>'
                    f'<path d="M13.5 9.8v7.4M9.8 13.5h7.4" stroke="{MIEL}" stroke-width="2.2" '
                    f'stroke-linecap="round"/>'), (13.5, 13.5)),
    "zoom-out": (svg(f'<circle cx="13.5" cy="13.5" r="8" fill="{BLANC}" stroke="{PRUNE}" stroke-width="2.2"/>'
                     f'<path d="M19.6 19.6l7 7" stroke="{PRUNE}" stroke-width="3.4" stroke-linecap="round"/>'
                     f'<path d="M9.8 13.5h7.4" stroke="{MIEL}" stroke-width="2.2" stroke-linecap="round"/>'),
                 (13.5, 13.5)),
}

# Noms supplémentaires attendus par les applications (X11, CSS, Qt, GTK, empreintes Qt)
ALIAS = {
    "default": ["left_ptr", "arrow", "top_left_arrow", "left_arrow", "right_ptr"],
    "pointer": ["hand1", "hand2", "pointing_hand", "9d800788f1b08800ae810202380a0822",
                "e29285e634086352946a0e7090d73106"],
    "grab": ["openhand", "fleur-open", "5aca4d189052212118709018842178c0"],
    "grabbing": ["closedhand", "dnd-none", "208530c400c041818281048008011002"],
    "text": ["xterm", "ibeam", "vertical-text"],
    "crosshair": ["cross", "tcross", "cross_reverse", "diamond_cross"],
    "not-allowed": ["forbidden", "crossed_circle", "no-drop", "dnd-no-drop", "circle",
                    "03b6e0fcb3499374a867c041f52298f0"],
    "help": ["question_arrow", "whats_this", "left_ptr_help", "5c6cd98b3f3ebcb1f9c7f1c204630408",
             "d9ce0ab605698f320427677b458ad60b"],
    "copy": ["dnd-copy", "1081e37283d90000800003c07f3ef6bf", "6407b0e94181790501fd1e167b474872"],
    "alias": ["link", "dnd-link", "3085a0e285430894940527032f8b26df", "640fb0e74195791501fd1ed57b41487f"],
    "context-menu": [],
    "move": ["fleur", "size_all", "all-scroll", "dnd-move", "4498f0e0c1937ffe01fd06f973665830",
             "9081237383d90e509aa00f00170e968f"],
    "ns-resize": ["n-resize", "s-resize", "size_ver", "sb_v_double_arrow", "v_double_arrow", "row-resize",
                  "split_v", "top_side", "bottom_side", "00008160000006810000408080010102",
                  "2870a09082c103050810ffdffffe0204"],
    "ew-resize": ["e-resize", "w-resize", "size_hor", "sb_h_double_arrow", "h_double_arrow", "col-resize",
                  "split_h", "left_side", "right_side", "028006030e0e7ebffc7f7070c0600140",
                  "14fef782d02440884392942c11205230"],
    "nesw-resize": ["ne-resize", "sw-resize", "size_bdiag", "fd_double_arrow", "top_right_corner",
                    "bottom_left_corner", "fcf1c3c7cd4491d801f1e1c78f100000", "50585d75b494802d0151028115016902"],
    "nwse-resize": ["nw-resize", "se-resize", "size_fdiag", "bd_double_arrow", "top_left_corner",
                    "bottom_right_corner", "c7088f0f3e6c8088236ef8e1e3e70000", "38c5dff7c7b8962045400281044508d2"],
    "wait": ["watch"],
    "progress": ["left_ptr_watch", "half-busy", "3ecb610c1bf2410f44200f48c40d3599",
                 "08e8e1c95fe2fc01f976f1e063a24ccd"],
    "cell": ["plus"],
    "zoom-in": [],
    "zoom-out": [],
}


def rendu(svg_txt, taille):
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as f:
        f.write(svg_txt)
    png = subprocess.run(["rsvg-convert", "-w", str(taille), "-h", str(taille), f.name],
                         capture_output=True, check=True).stdout
    os.unlink(f.name)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def xcursor(images):
    """images : [(nominal, Image RGBA, (hx, hy), délai)] → octets d'un fichier Xcursor."""
    entetes, corps = [], []
    position = 16 + 12 * len(images)
    for nominal, im, (hx, hy), delai in images:
        w, h = im.size
        px = bytearray()
        brut = im.convert("RGBA").tobytes()
        for i in range(0, len(brut), 4):                 # ARGB prémultiplié, petit-boutiste
            r, g, b, a = brut[i:i + 4]
            px += bytes((b * a // 255, g * a // 255, r * a // 255, a))
        bloc = struct.pack("<IIIIIIIII", 36, 0xFFFD0002, nominal, 1, w, h, hx, hy, delai) + bytes(px)
        entetes.append(struct.pack("<III", 0xFFFD0002, nominal, position))
        corps.append(bloc)
        position += len(bloc)
    return b"Xcur" + struct.pack("<III", 16, 0x10000, len(images)) + b"".join(entetes) + b"".join(corps)


def generer():
    dossier = os.path.join(SORTIE, "cursors")
    os.makedirs(dossier, exist_ok=True)
    for f in os.listdir(dossier):
        os.unlink(os.path.join(dossier, f))
    for nom, spec in FORMES.items():
        source, (hx, hy) = spec[0], spec[1]
        delai = spec[2] if len(spec) > 2 else 0
        cadres = source if isinstance(source, list) else [source]
        images = []
        for t in TAILLES:
            k = t / 32
            for c in cadres:
                images.append((t, rendu(c, t), (round(hx * k), round(hy * k)), delai))
        with open(os.path.join(dossier, nom), "wb") as f:
            f.write(xcursor(images))
        for a in ALIAS.get(nom, []):
            os.symlink(nom, os.path.join(dossier, a))
    with open(os.path.join(SORTIE, "index.theme"), "w") as f:
        f.write("[Icon Theme]\nName=NounoursOS\nComment=Curseur NounoursOS : flèche prune et miel\n"
                "Inherits=breeze_cursors\n")
    with open(os.path.join(SORTIE, "cursor.theme"), "w") as f:
        f.write("[Icon Theme]\nInherits=NounoursOS\n")
    # Aperçu (pour Paramètres et la documentation)
    noms = ["default", "pointer", "text", "wait", "progress", "move", "ew-resize", "not-allowed", "help", "copy"]
    ap = Image.new("RGBA", (len(noms) * 56, 56), (0, 0, 0, 0))
    for i, n in enumerate(noms):
        s = FORMES[n][0]
        ap.alpha_composite(rendu(s[3] if isinstance(s, list) else s, 48), (i * 56 + 4, 4))
    ap.save(os.path.join(SORTIE, "apercu.png"))
    print(len(FORMES), "formes,", sum(len(v) for v in ALIAS.values()), "alias →", SORTIE)


if __name__ == "__main__":
    generer()
