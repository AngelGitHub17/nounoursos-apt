#!/usr/bin/env python3
"""Génère les icônes des Paramètres NounoursOS (SVG) : pastille colorée + pictogramme blanc.
Usage : python3 iso/assets/icones.py  -> iso/desktop/includes.chroot/usr/share/nounoursos/icones/"""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "desktop", "includes.chroot", "usr", "share", "nounoursos", "icones")

BLUE, RED, ORANGE, GREEN, PURPLE, GREY, PINK, TEAL, PLUM, HONEY, INDIGO, YELLOW = (
    "#3D7EDB", "#E5484D", "#E8833A", "#3FA36B", "#7E57C2", "#7C7586", "#D9568C", "#2BA3A3",
    "#4B3766", "#D98A3F", "#5B5BD6", "#E0A400")

S = 'fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
F = 'fill="#fff"'
S3 = S.replace('stroke-width="2"', 'stroke-width="2.6"')

# Pictogrammes dessinés dans une grille 24x24
GLYPHS = {
    "wifi": (BLUE, f'<path {S} d="M3.5 9.5a12 12 0 0 1 17 0M6.5 12.8a7.5 7.5 0 0 1 11 0M9.5 16a3 3 0 0 1 5 0"/><circle {F} cx="12" cy="19" r="1.6"/>'),
    "bluetooth": (BLUE, f'<path {S} d="M7 7.5l10 9-5 4.5V3l5 4.5-10 9"/>'),
    "reseau": (BLUE, f'<rect {S} x="9" y="3" width="6" height="5" rx="1.2"/><rect {S} x="3" y="16" width="6" height="5" rx="1.2"/><rect {S} x="15" y="16" width="6" height="5" rx="1.2"/><path {S} d="M12 8v4M6 16v-4h12v4"/>'),
    "notifications": (RED, f'<path {S} d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 1.5h-15z"/><path {S} d="M10 20.5a2.2 2.2 0 0 0 4 0"/>'),
    "son": (RED, f'<path {F} d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path {S} d="M15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11"/>'),
    "maj": (GREY, f'<path {S} d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3"/><path {S} d="M18.5 3.8v3.6h-3.6"/><path {S} d="M12 8v7.5M9 12.8l3 3 3-3"/>'),
    "apropos": (GREY, f'<circle {S} cx="12" cy="12" r="8.5"/><path {S} d="M12 11v5.5"/><circle {F} cx="12" cy="7.8" r="1.4"/>'),
    "windows": (INDIGO, f'<rect {S} x="3" y="4" width="18" height="13.5" rx="2"/><path {S} d="M8.5 20.5h7"/><rect {F} x="7.5" y="7" width="4" height="3.4" rx="0.6"/><rect {F} x="12.5" y="7" width="4" height="3.4" rx="0.6"/><rect {F} x="7.5" y="11.2" width="4" height="3.4" rx="0.6"/><rect {F} x="12.5" y="11.2" width="4" height="3.4" rx="0.6"/>'),
    "apparence": (PLUM, f'<circle {S} cx="12" cy="12" r="8.5"/><path {F} d="M12 3.5a8.5 8.5 0 0 1 0 17z"/>'),
    "bureau": (PLUM, f'<rect {S} x="3" y="4" width="18" height="13" rx="2"/><path {S} d="M8.5 20.5h7"/><rect {F} x="7" y="13" width="10" height="2" rx="1"/>'),
    "fond": (TEAL, f'<rect {S} x="3" y="5" width="18" height="14" rx="2"/><path {S} d="M3.5 17l5-5.5 4 4 2.5-2.5 5.5 5.5"/><circle {F} cx="15.5" cy="9" r="1.7"/>'),
    "ecrans": (BLUE, f'<rect {S} x="3" y="4" width="18" height="12" rx="2"/><path {S} d="M12 16v4M8 20.5h8"/>'),
    "polices": (GREY, f'<path {S} d="M2.5 18.5L7 6h1l4.5 12.5M4.2 14h6.6"/><circle {S} cx="17.3" cy="15.3" r="3.2"/><path {S} d="M20.5 12v6.5"/>'),
    "couleurs": (PINK, f'<circle {S} cx="12" cy="8.5" r="4.5"/><circle {S} cx="8.5" cy="14.5" r="4.5"/><circle {S} cx="15.5" cy="14.5" r="4.5"/>'),
    "icones": (ORANGE, f'<rect {F} x="4" y="4" width="6.5" height="6.5" rx="1.8"/><rect {F} x="13.5" y="4" width="6.5" height="6.5" rx="1.8"/><rect {F} x="4" y="13.5" width="6.5" height="6.5" rx="1.8"/><rect {S} x="13.5" y="13.5" width="6.5" height="6.5" rx="1.8"/>'),
    "pointeur": (GREY, f'<path fill="#fff" stroke="#fff" stroke-width="1.5" stroke-linejoin="round" d="M6 3.5l12 8.2-5.2 1 3 6-2.5 1.2-3-6-4.3 3.6z"/>'),
    "effets": (PURPLE, f'<path {F} d="M10 3l1.8 5.2L17 10l-5.2 1.8L10 17l-1.8-5.2L3 10l5.2-1.8zM17.5 13.5l.9 2.6 2.6.9-2.6.9-.9 2.6-.9-2.6-2.6-.9 2.6-.9z"/>'),
    "splash": (PURPLE, f'<path {S} d="M12 3.5a8.5 8.5 0 1 1-8.5 8.5"/><circle {F} cx="12" cy="12" r="2.2"/>'),
    "fenetres": (GREY, f'<rect {S} x="3" y="3.5" width="13" height="10" rx="1.8"/><rect fill="#fff" fill-opacity="0.35" stroke="#fff" stroke-width="2" x="8" y="10.5" width="13" height="10" rx="1.8"/>'),
    "bureaux": (GREY, f'<rect {S} x="3" y="4" width="8" height="6.5" rx="1.5"/><rect {F} x="13" y="4" width="8" height="6.5" rx="1.5"/><rect {S} x="3" y="13.5" width="8" height="6.5" rx="1.5"/><rect {S} x="13" y="13.5" width="8" height="6.5" rx="1.5"/>'),
    "raccourcis": (GREY, f'<path {S} d="M9 9V6.8A2.3 2.3 0 1 0 6.8 9H9zm0 0h6m-6 0v6m6-6V6.8A2.3 2.3 0 1 1 17.2 9H15zm0 0v6m0 0h-6m6 0v2.2a2.3 2.3 0 1 0 2.2-2.2H15zm-6 0v2.2A2.3 2.3 0 1 1 6.8 15H9z"/>'),
    "recherche": (GREY, f'<circle {S} cx="10.5" cy="10.5" r="6"/><path {S3} d="M15 15l5 5"/>'),
    "verrouillage": (GREY, f'<rect {F} x="5" y="10.5" width="14" height="10" rx="2"/><path {S} d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/>'),
    "utilisateurs": (GREY, f'<circle {F} cx="12" cy="8.5" r="4"/><path {F} d="M4.5 20a7.5 7.5 0 0 1 15 0z"/>'),
    "connexion": (GREY, f'<path {S} d="M14 4h4.5a1.5 1.5 0 0 1 1.5 1.5v13a1.5 1.5 0 0 1-1.5 1.5H14"/><path {S} d="M4 12h11M11 8l4 4-4 4"/>'),
    "energie": (GREEN, f'<rect {S} x="3" y="7.5" width="16" height="9" rx="2"/><path {S} d="M21 10.5v3"/><rect {F} x="5.5" y="10" width="7" height="4" rx="0.8"/>'),
    "accessibilite": (BLUE, f'<circle {F} cx="12" cy="5" r="2"/><path {S} d="M5 8.5l7 1.5 7-1.5M12 10v4.5l-3 6M12 14.5l3 6"/>'),
    "langue": (BLUE, f'<circle {S} cx="12" cy="12" r="8.5"/><path {S} d="M3.5 12h17M12 3.5c3 3.2 3 13.8 0 17M12 3.5c-3 3.2-3 13.8 0 17"/>'),
    "date": (BLUE, f'<circle {S} cx="12" cy="12" r="8.5"/><path {S} d="M12 7v5.2l3.5 2.3"/>'),
    "clavier": (GREY, f'<rect {S} x="2.5" y="6" width="19" height="12" rx="2"/><path {S3} d="M6 10h.01M9.3 10h.01M12.6 10h.01M15.9 10h.01M8 14.2h8"/>'),
    "souris": (GREY, f'<rect {S} x="6.5" y="3" width="11" height="18" rx="5.5"/><path {S} d="M12 7v3"/>'),
    "pave": (GREY, f'<rect {S} x="3" y="4" width="18" height="16" rx="2.5"/><path {S} d="M3.5 15h17M12 15v4.5"/>'),
    "imprimantes": (GREY, f'<path {S} d="M7 9V3.5h10V9"/><rect {S} x="3" y="9" width="18" height="8" rx="2"/><rect {F} x="7" y="14" width="10" height="7" rx="1"/>'),
    "applis": (ORANGE, f'<rect {S} x="4" y="4" width="6.5" height="6.5" rx="1.8"/><rect {S} x="13.5" y="4" width="6.5" height="6.5" rx="1.8"/><rect {S} x="4" y="13.5" width="6.5" height="6.5" rx="1.8"/><path {F} d="M16.75 12.6l1.1 2.3 2.5.3-1.8 1.7.5 2.5-2.3-1.2-2.2 1.2.4-2.5-1.8-1.7 2.5-.3z"/>'),
    "fichiers": (BLUE, f'<path {S} d="M6 3h8l4.5 4.5V21H6z"/><path {S} d="M14 3v4.5h4.5M9 13h6M9 16.5h6"/>'),
    "demarrage": (GREEN, f'<circle {S} cx="12" cy="12" r="8.5"/><path {F} d="M10 8l6 4-6 4z"/>'),
    "session": (RED, f'<path {S} d="M12 3.5v8"/><path {S} d="M7.3 6.5a7.5 7.5 0 1 0 9.4 0"/>'),
    "disques": (GREY, f'<rect {S} x="3" y="7" width="18" height="10" rx="2.5"/><circle {F} cx="17" cy="12" r="1.5"/><path {S} d="M6.5 12h6"/>'),
    "veille": (INDIGO, f'<path {F} d="M15.5 3.5a8.5 8.5 0 1 0 5 13.3 7 7 0 0 1-5-13.3z"/><path {F} d="M8 5l.6 1.6 1.6.6-1.6.6L8 9.4l-.6-1.6L5.8 7.2l1.6-.6z"/>'),
    "empreinte": (PINK, f'<path {S} d="M5.5 9.5a7 7 0 0 1 13 0"/><path {S} d="M8.2 18.5c1-1.8 1.3-3.7 1.3-6.5a2.5 2.5 0 0 1 5 0c0 3-.4 5.4-1.6 7.8"/><path {S} d="M12 12c0 3.2-.6 6-2.2 8.3"/><path {S} d="M17.5 13.5c-.2 2.2-.7 4-1.5 5.6"/><path {S} d="M5.2 14c.6-1.1.9-2.3.9-3.6"/>'),
    "capsule": (TEAL, f'<path {S} d="M4.6 13.5A7.6 7.6 0 1 0 6.8 6.5"/><path {S} d="M6.6 2.8v3.9h3.9"/><path {S} d="M12 8v4.6l3.1 2"/>'),
    "jeu": (GREEN, f'<path {S} d="M7.5 7.5h9a4.5 4.5 0 0 1 4.3 5.8l-1.1 3.9a2.3 2.3 0 0 1-3.9.9L13.7 16h-3.4l-2.1 2.1a2.3 2.3 0 0 1-3.9-.9l-1.1-3.9a4.5 4.5 0 0 1 4.3-5.8z"/><path {S} d="M8 10.3v3.4M6.3 12h3.4"/><circle {F} cx="15.6" cy="11" r="1.1"/><circle {F} cx="17.4" cy="13.3" r="1.1"/>'),
    "telephone": (GREEN, f'<rect {S} x="6.5" y="2.8" width="11" height="18.4" rx="2.6"/><path {S3} d="M10.5 18h3"/>'),
    "nettoyage": (TEAL, f'<path {S} d="M14.5 3.5l-3.2 7.2"/><path {F} d="M8.2 10.2h7.6l1.6 2.4-1.5 8H8.1l-1.5-8z"/><path fill="none" stroke="{TEAL}" stroke-width="1.6" stroke-linecap="round" d="M10.3 14.5v3.5M13.7 14.5v3.5"/>'),
    "partage": (BLUE, f'<path {S} d="M20.5 3.5L10.2 13.8"/><path {S} d="M20.5 3.5l-6.6 17-3.7-7.2-7.2-3.7z"/>'),
    "compte": (HONEY, f'<circle {S} cx="12" cy="9" r="3.6"/><path {S} d="M5.2 19.5a6.8 6.8 0 0 1 13.6 0"/><circle {F} cx="8.6" cy="5.2" r="1.5"/><circle {F} cx="15.4" cy="5.2" r="1.5"/>'),
    "concentration": (INDIGO, f'<path {F} d="M14.8 3.2a8.8 8.8 0 1 0 6 11.9A7 7 0 0 1 14.8 3.2z"/>'),
    "migration": (BLUE, f'<rect {S} x="2.8" y="5" width="8.4" height="8.4" rx="1.2"/><path {S} d="M7 5v8.4M2.8 9.2h8.4"/><path {S} d="M13.5 15.5h7.7M17.8 12l3.4 3.5-3.4 3.5"/><path {S} d="M7 16.5v2.8h4.5"/>'),
    "retour": ("#C2410C", f'<path {S} d="M4.5 9.5A8 8 0 1 1 4 14"/><path {S} d="M3.6 4.8v4.9h4.9"/><path {S} d="M12 8v4.5l3 1.8"/>'),
    "minecraft": ("#3F8E3C", f'<path {S} d="M12 2.8 20 7.2v9.6L12 21.2 4 16.8V7.2z"/><path {S} d="M4 7.2 12 11.6 20 7.2M12 11.6v9.6"/><path {S} d="M8 9.4v3M16 9.4v3M8.6 15.6l1.6.9"/>'),
    "tous": (GREY, f'<path {S} d="M12 2.8l1.6 2.5 2.9-.6.6 2.9 2.5 1.6-1.5 2.6 1.5 2.6-2.5 1.6-.6 2.9-2.9-.6-1.6 2.5-1.6-2.5-2.9.6-.6-2.9-2.5-1.6 1.5-2.6-1.5-2.6 2.5-1.6.6-2.9 2.9.6z"/><circle {S} cx="12" cy="12" r="3"/>'),
}


def svg(color, glyph):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{color}" stop-opacity="0.82"/><stop offset="1" stop-color="{color}"/>
  </linearGradient></defs>
  <rect width="64" height="64" rx="15" fill="{color}"/>
  <rect width="64" height="64" rx="15" fill="url(#g)"/>
  <rect x="0.75" y="0.75" width="62.5" height="62.5" rx="14.5" fill="none" stroke="#000" stroke-opacity="0.10" stroke-width="1.5"/>
  <g transform="translate(12 12) scale(1.6667)">{glyph}</g>
</svg>
'''


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, (color, glyph) in GLYPHS.items():
        with open(os.path.join(OUT, name + ".svg"), "w") as f:
            f.write(svg(color, glyph))
    print(len(GLYPHS), "icônes dans", os.path.normpath(OUT))
