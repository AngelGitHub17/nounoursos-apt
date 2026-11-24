#!/usr/bin/env python3
"""Thèmes de couleur NounoursOS.

Génère, pour chaque variante (Miel, Myrtille, Lavande, Menthe, Framboise, Graphite) :
  - deux schémas de couleurs KDE (clair et sombre) à partir de Breeze, avec fonds
    teintés NounoursOS (crème en clair, prune en sombre) et la couleur d'accent ;
  - un fond d'écran assorti (paquet de fond d'écran Plasma).
Usage : python3 iso/assets/make-themes.py   (rsvg-convert requis pour les fonds)
"""
import os
import re
import subprocess

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.join(ICI, "..", "desktop", "includes.chroot", "usr", "share")

# nom, accent, lien (clair), lien (sombre), lueur du fond d'écran
VARIANTES = [
    ("Miel", (217, 138, 63), (160, 98, 42), (245, 184, 98), "#F5B862"),
    ("Myrtille", (61, 126, 219), (38, 96, 180), (122, 172, 245), "#8DB8F5"),
    ("Lavande", (126, 87, 194), (98, 62, 165), (178, 150, 232), "#C2A8F0"),
    ("Menthe", (63, 163, 107), (40, 128, 80), (120, 214, 160), "#8FE0B2"),
    ("Framboise", (217, 86, 140), (180, 56, 108), (240, 140, 182), "#F5A3C4"),
    ("Graphite", (107, 100, 120), (82, 76, 94), (176, 168, 190), "#C9C2D4"),
]
BREEZE_ACCENT = "61,174,233"
BREEZE_LIENS = ("41,128,185", "29,153,243")
FONDS = ("Window", "View", "Button", "Header", "Header][Inactive", "Tooltip", "Complementary")


def rgb(t):
    return ",".join(str(max(0, min(255, int(v)))) for v in t)


def teinter(valeur, sombre):
    r, g, b = (int(x) for x in valeur.split(","))
    if sombre:                       # prune : un peu plus de rouge et de bleu
        return rgb((r + 3, g - 4, b + 6))
    return rgb((r + 4, g - 1, b - 8))  # crème : un peu plus chaud


def schema(base, nom, accent, lien, sombre):
    out, section = [], ""
    for line in open(base, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("["):
            section = line.strip("[]")
            out.append(line)
            continue
        if "=" not in line:
            out.append(line)
            continue
        key, val = line.split("=", 1)
        if section == "General" and (key == "Name" or key.startswith("Name[")):
            if key != "Name":
                continue                       # pas de traductions de « Breeze »
            val = f"NounoursOS {nom} ({'sombre' if sombre else 'clair'})"
        elif section == "General" and key == "ColorScheme":
            val = f"NounoursOS{nom}{'Sombre' if sombre else 'Clair'}"
        elif section == "Colors:Selection" and key == "BackgroundAlternate":
            val = rgb(tuple(c * 0.55 for c in accent)) if sombre else rgb(tuple(c * 0.85 for c in accent))
        elif section.replace("Colors:", "") in FONDS and key.startswith("Background") \
                and val != BREEZE_ACCENT and section != "Colors:Selection":
            val = teinter(val, sombre)
        if val == BREEZE_ACCENT:
            val = rgb(accent)
        elif val in BREEZE_LIENS:
            val = rgb(lien)
        out.append(f"{key}={val}")
    return "\n".join(out) + "\n"


def fond(nom, accent, lueur):
    """Fond « Origami » de l'identité NounoursOS, aux couleurs de la teinte."""
    import sys
    sys.path.insert(0, ICI)
    from identite import fond_svg
    d = os.path.join(RACINE, "wallpapers", f"NounoursOS-{nom}")
    images = os.path.join(d, "contents", "images")
    os.makedirs(images, exist_ok=True)
    svg = fond_svg(accent="#%02X%02X%02X" % accent, lueur=lueur, graine=17)
    tmp = "/tmp/nounoursos-fond.svg"
    with open(tmp, "w") as f:
        f.write(svg)
    for w, h in ((1920, 1080), (3840, 2160)):
        subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), tmp, "-o", f"{images}/{w}x{h}.png"], check=True)
    subprocess.run(["rsvg-convert", "-w", "400", "-h", "225", tmp, "-o", f"{d}/contents/screenshot.png"], check=True)
    with open(os.path.join(d, "metadata.json"), "w") as f:
        f.write('{\n    "KPlugin": {\n        "Authors": [ { "Name": "NounoursCorp" } ],\n'
                f'        "Id": "NounoursOS-{nom}",\n        "License": "CC-BY-SA-4.0",\n'
                f'        "Name": "NounoursOS {nom}"\n    }}\n}}\n')


if __name__ == "__main__":
    cs = os.path.join(RACINE, "color-schemes")
    os.makedirs(cs, exist_ok=True)
    for nom, accent, lien_c, lien_s, lueur in VARIANTES:
        for sombre in (False, True):
            base = os.path.join(ICI, "breeze", "BreezeDark.colors" if sombre else "BreezeLight.colors")
            fichier = f"NounoursOS{nom}{'Sombre' if sombre else 'Clair'}.colors"
            with open(os.path.join(cs, fichier), "w", encoding="utf-8") as f:
                f.write(schema(base, nom, accent, lien_s if sombre else lien_c, sombre))
        if nom != "Miel":                      # Miel = fond NounoursOS d'origine
            fond(nom, accent, lueur)
    print(len(VARIANTES) * 2, "schémas de couleurs +", len(VARIANTES) - 1, "fonds d'écran")
