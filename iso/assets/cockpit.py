#!/usr/bin/env python3
"""Identité NounoursOS pour Cockpit (NounoursOS Server) : page de connexion et icônes.

Cockpit cherche /usr/share/cockpit/branding/<ID de os-release> : ici « nounoursos ».
Sortie : server/includes.chroot/usr/share/cockpit/branding/nounoursos/
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from identite import ISO, MIEL_CLAIR, NUIT, CREME, fond_svg, logo_svg, png  # noqa: E402

SORTIE = os.path.join(ISO, "server", "includes.chroot", "usr", "share", "cockpit", "branding", "nounoursos")

CSS = f"""/* NounoursOS Server — généré par iso/assets/cockpit.py */
#badge {{
    inline-size: 96px;
    block-size: 96px;
    background-image: url("logo.png");
    background-size: contain;
    background-repeat: no-repeat;
}}

#brand::before {{
    content: "NounoursOS Server";
    font-weight: 700;
}}

body.login-pf {{
    background: {NUIT} url("fond.jpg") center / cover no-repeat;
    color: {CREME};
}}

body.login-pf #brand {{
    color: #FFFFFF;
}}

body.login-pf #login-button {{
    background-color: {MIEL_CLAIR};
    border-color: {MIEL_CLAIR};
    color: {NUIT};
}}
"""


def generer():
    os.makedirs(SORTIE, exist_ok=True)
    png(logo_svg(), f"{SORTIE}/logo.png", 256, 256)
    png(logo_svg(), f"{SORTIE}/apple-touch-icon.png", 180, 180)
    png(fond_svg(1920, 1080, graine=73, nuit=0.1), "/tmp/nounoursos-cockpit-fond.png", 1920, 1080)
    from PIL import Image
    Image.open("/tmp/nounoursos-cockpit-fond.png").convert("RGB").save(f"{SORTIE}/fond.jpg", quality=86,
                                                                       optimize=True, progressive=True)
    os.unlink("/tmp/nounoursos-cockpit-fond.png")
    Image.open(f"{SORTIE}/logo.png").save(f"{SORTIE}/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    with open(f"{SORTIE}/branding.css", "w", encoding="utf-8") as f:
        f.write(CSS)
    print(f"Cockpit : {SORTIE}")


if __name__ == "__main__":
    generer()
