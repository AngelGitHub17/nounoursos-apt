#!/usr/bin/env python3
"""NounoursNT : construit à partir des sources de LiberNT, aux couleurs de NounoursOS.

La politique de marque de LiberNT (TRADEMARK.md) demande qu'une version modifiée
ne s'appelle pas LiberNT et n'embarque pas son logo (qui n'est pas sous GPL).
Ce script, lancé sur une copie des sources de LiberNT :
  1. remplace « LiberNT » par « NounoursNT » dans les textes AFFICHÉS uniquement
     (ressources .rc/.mc, valeurs des .inf, messages du code). Les commentaires,
     les en-têtes de copyright et les chemins internes (EFI\\LiberNT, clés de
     registre…) ne sont pas touchés : l'attribution reste, le démarrage aussi ;
  2. remplace chaque image portant le logo LiberNT par l'ourson NounoursOS, à la
     même taille, au même format et avec la même palette ;
  3. ajoute une mention « basé sur les sources de LiberNT ».

Usage : python3 nounoursnt/rebaptiser.py <dossier des sources LiberNT>
Requiert rsvg-convert, Pillow et la police Inter.
"""
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image, ImageFilter

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "iso", "assets"))
import identite as ID  # noqa: E402

ANCIEN, NOUVEAU = "LiberNT", "NounoursNT"


# --- 1. Textes ------------------------------------------------------------------------
LITTERAL = re.compile(r'(L?)"((?:[^"\\\n]|\\.)*)"')


def _texte_affiche(contenu):
    """Un littéral C est du texte affiché s'il contient une phrase ou un nom de touche."""
    if ANCIEN not in contenu or "\\\\" in contenu or "\\" in contenu.replace("\\n", "").replace("\\r", "") \
            .replace("\\t", "").replace('\\"', ""):
        return False
    return " " in contenu or f"<{ANCIEN}>" in contenu


def renommer_c(texte):
    def rempl(m):
        if _texte_affiche(m.group(2)):
            return f'{m.group(1)}"{m.group(2).replace(ANCIEN, NOUVEAU)}"'
        return m.group(0)
    out = []
    for ligne in texte.split("\n"):
        s = ligne.lstrip()
        # Lignes de commentaire (en-têtes PROJECT/COPYRIGHT…) : on ne touche à rien
        if s.startswith(("*", "/*", "//", "#include")):
            out.append(ligne)
        else:
            out.append(LITTERAL.sub(rempl, ligne))
    return "\n".join(out)


def renommer_rc(texte):
    def rempl(m):
        return f'{m.group(1)}"{m.group(2).replace(ANCIEN, NOUVEAU)}"' if ANCIEN in m.group(2) else m.group(0)
    out = []
    for ligne in texte.split("\n"):
        s = ligne.lstrip()
        if s.startswith(("*", "/*", "//", "#include")):
            out.append(ligne)
        else:
            out.append(LITTERAL.sub(rempl, ligne))
    return "\n".join(out)


def _champs(ligne):
    """Découpe une ligne .inf aux virgules hors guillemets (positions de début/fin)."""
    champs, debut, dedans = [], 0, False
    for i, c in enumerate(ligne):
        if c == '"':
            dedans = not dedans
        elif c == "," and not dedans:
            champs.append((debut, i))
            debut = i + 1
    champs.append((debut, len(ligne)))
    return champs


def renommer_inf(texte):
    out, section = [], ""
    for ligne in texte.split("\n"):
        s = ligne.strip()
        if s.startswith("[") and "]" in s:
            section = s[1:s.index("]")].lower()
            out.append(ligne)
            continue
        if ANCIEN not in ligne or s.startswith(";"):
            out.append(ligne)
            continue
        if section.startswith("strings"):
            # nom = "valeur" : seule la valeur est affichée
            if "=" in ligne:
                k, v = ligne.split("=", 1)
                ligne = k + "=" + v.replace(ANCIEN, NOUVEAU)
        elif re.match(r'\s*(HKLM|HKCU|HKCR|HKU|HKR|BCD)\s*,', ligne):
            # Registre : la clé et le nom de valeur restent, seule la DONNÉE (5e champ et +) change
            ch = _champs(ligne)
            if len(ch) >= 5:
                d = ch[4][0]
                ligne = ligne[:d] + ligne[d:].replace(ANCIEN, NOUVEAU)
        out.append(ligne)
    return "\n".join(out)


def renommer_textes(racine):
    compte = {}
    for dossier, sous, fichiers in os.walk(racine):
        sous[:] = [d for d in sous if d not in (".git", "output-Clang-amd64-debug")]
        for f in fichiers:
            chemin = os.path.join(dossier, f)
            ext = f.lower().rsplit(".", 1)[-1] if "." in f else ""
            if f.lower().endswith(".inf.in"):
                ext = "inf"
            fonction = {"c": renommer_c, "cpp": renommer_c, "h": renommer_c, "hpp": renommer_c,
                        "rc": renommer_rc, "inf": renommer_inf}.get(ext)
            if ext == "mc":
                fonction = lambda t: t.replace(ANCIEN, NOUVEAU)  # noqa: E731  (texte des messages)
            if not fonction:
                continue
            try:
                with open(chemin, encoding="utf-8", errors="surrogateescape", newline="") as fh:
                    avant = fh.read()
            except OSError:
                continue
            if ANCIEN not in avant:
                continue
            apres = fonction(avant)
            if apres != avant:
                with open(chemin, "w", encoding="utf-8", errors="surrogateescape", newline="") as fh:
                    fh.write(apres)
                compte[ext] = compte.get(ext, 0) + 1
    return compte


# Noms affichés qui ne sont pas des phrases (titres, nom Bluetooth, étiquette…),
# et la détection de mise à niveau qui suit le nouveau nom du produit.
EXPLICITES = [
    ("base/applications/winver/winver.c", 'L"LiberNT"', 'L"NounoursNT"'),
    ("bootloader/bootmgr/main.c", 'BM_LIBERNT_TITLE   L"LiberNT"', 'BM_LIBERNT_TITLE   L"NounoursNT"'),
    ("bootloader/gui/bootui.c", '"LiberNT"', '"NounoursNT"'),
    ("drivers/bluetooth/bthmini/hci.c", '"LiberNT"', '"NounoursNT"'),
    ("dll/win32/windowscodecs/regsvr.c", '"LiberNT"', '"NounoursNT"'),
    ("drivers/base/vmic/vmic.c", 'L"LiberNT"', 'L"NounoursNT"'),
    ("subsystems/linux/lxwayland/lxwayland.c", '"LiberNT", "Desktop"', '"NounoursNT", "Desktop"'),
    ("base/setup/libernt/hostpage.c", 'HOST_PARTITION_LABEL    L"LiberNT"', 'HOST_PARTITION_LABEL    L"NounoursNT"'),
    ("base/setup/libernt/upgrade.c", 'wcsstr(Product, L"LiberNT")', 'wcsstr(Product, L"NounoursNT")'),
    ("image/images.cmake", 'set(ISO_MANUFACTURER "LiberNT Project")', 'set(ISO_MANUFACTURER "NounoursCorp")'),
    ("image/images.cmake", 'set(ISO_VOLNAME      "LiberNT")', 'set(ISO_VOLNAME      "NounoursNT")'),
    ("image/images.cmake", '"-DINVENTORY_HEADER=LiberNT ', '"-DINVENTORY_HEADER=NounoursNT '),
]


def renommer_explicites(racine):
    manque = []
    for rel, avant, apres in EXPLICITES:
        chemin = os.path.join(racine, rel)
        try:
            with open(chemin, encoding="utf-8", errors="surrogateescape", newline="") as f:
                t = f.read()
        except OSError:
            manque.append(rel)
            continue
        if avant not in t:
            manque.append(f"{rel} ({avant})")
            continue
        with open(chemin, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
            f.write(t.replace(avant, apres))
    return manque


# --- 2. Images -------------------------------------------------------------------------
NUIT = ID.NUIT


def _largeur_texte(taille):
    """Largeur réelle de « NounoursNT » en Inter Display (Bold + ExtraBold)."""
    from PIL import ImageFont
    try:
        chemin = subprocess.run(["fc-match", "-f", "%{file}", "Inter Display:bold"],
                                capture_output=True, text=True).stdout
        chemin2 = subprocess.run(["fc-match", "-f", "%{file}", "Inter Display:extrabold"],
                                 capture_output=True, text=True).stdout
        a = ImageFont.truetype(chemin, 200).getlength("Nounours")
        b = ImageFont.truetype(chemin2, 200).getlength("NT")
        return (a + b) / 200 * taille - taille * 0.02 * 9
    except Exception:
        return taille * 5.6


def _svg_marque(w, h, fond=None, texte=True, couleur="#FFFFFF", logo=None, x_logo=None, taille_txt=None,
                vertical=False):
    """Ourson (+ « NounoursNT ») centré dans un cadre w×h."""
    corps = f'<rect width="{w}" height="{h}" fill="{fond}"/>' if fond else ""
    if vertical:
        k = min(w * 0.8, h * 0.18)
        corps += ID.logo_groupe((w - k) / 2, h - k - w * 0.15, k)
        if texte:
            t = taille_txt or w * 0.42
            corps += (f'<text transform="translate({w / 2 + t * 0.36:.1f} {h - k - w * 0.4:.1f}) rotate(-90)" '
                      f'font-family="Inter Display, Inter, sans-serif" font-size="{t:.1f}" font-weight="700" '
                      f'fill="{couleur}">Nounours<tspan fill="{ID.MIEL_CLAIR}">NT</tspan></text>')
    elif texte:
        k = logo or h * 0.78
        t = taille_txt or h * 0.5
        # On réduit si l'ensemble ne tient pas dans 90 % de la largeur
        while k + t * 0.25 + _largeur_texte(t) > w * 0.9 and t > 4:
            t *= 0.94
            k *= 0.94
        largeur = k + t * 0.25 + _largeur_texte(t)
        x0 = x_logo if x_logo is not None else (w - largeur) / 2
        corps += ID.logo_groupe(x0, (h - k) / 2, k)
        corps += (f'<text x="{x0 + k + t * 0.25:.1f}" y="{h / 2 + t * 0.36:.1f}" '
                  f'font-family="Inter Display, Inter, sans-serif" font-size="{t:.1f}" font-weight="700" '
                  f'letter-spacing="{-t * 0.02:.1f}" fill="{couleur}">Nounours'
                  f'<tspan fill="{ID.MIEL if couleur != "#FFFFFF" else ID.MIEL_CLAIR}" font-weight="800">NT</tspan></text>')
    else:
        k = logo or min(w, h) * 0.86
        corps += ID.logo_groupe((w - k) / 2, (h - k) / 2, k)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{corps}</svg>'


def _rendu(svg, w, h):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    ID.png(svg, tmp, w, h)
    im = Image.open(tmp).convert("RGBA")
    im.load()
    os.unlink(tmp)
    return im


def _comme(original, nouvelle):
    """Enregistre `nouvelle` au même format que le fichier `original` (taille, mode, palette)."""
    ref = Image.open(original)
    ext = original.lower().rsplit(".", 1)[-1]
    if ext == "ico":
        tailles = sorted(ref.ico.sizes()) if hasattr(ref, "ico") else [ref.size]
        nouvelle.save(original, format="ICO", sizes=tailles)
        return
    nouvelle = nouvelle.resize(ref.size, Image.LANCZOS) if nouvelle.size != ref.size else nouvelle
    if ext == "png":
        nouvelle.save(original)
        return
    if ref.mode == "P":
        # Même nombre de couleurs que l'original (16 pour l'écran de démarrage VGA),
        # palette recalculée pour les tons miel de l'ourson
        n = len(ref.getpalette()) // 3
        fond = Image.new("RGB", nouvelle.size, (0, 0, 0))
        fond.paste(nouvelle, (0, 0), nouvelle)
        q = fond.quantize(colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        pal = (q.getpalette() or [])[:n * 3]
        q.putpalette(pal + [0] * (n * 3 - len(pal)))
        q.save(original, format="BMP")
    elif ref.mode == "RGBA":
        _bmp32(original, nouvelle)
    elif ref.mode == "L":
        nouvelle.convert("L").save(original, format="BMP")
    else:
        fond = Image.new("RGB", nouvelle.size, (0, 0, 0))
        fond.paste(nouvelle, (0, 0), nouvelle)
        fond.save(original, format="BMP")


def _bmp32(original, im):
    """BMP 32 bits avec transparence : on garde l'en-tête d'origine (V5, masques) et on
    remplace seulement les pixels (BGRA, même taille)."""
    import struct
    d = open(original, "rb").read()
    off = struct.unpack("<I", d[10:14])[0]
    w, h = struct.unpack("<ii", d[18:26])
    im = im.convert("RGBA").resize((w, abs(h)))
    lignes = [im.crop((0, y, w, y + 1)).tobytes("raw", "BGRA") for y in range(abs(h))]
    if h > 0:                       # stocké de bas en haut
        lignes.reverse()
    with open(original, "wb") as f:
        f.write(d[:off] + b"".join(lignes))


def _masque(im, flou=6):
    """Masque blanc/noir à bord doux, à partir de la transparence (comme rosbitmap_mask)."""
    a = im.getchannel("A").point(lambda v: 255 if v > 20 else 0)
    return a.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(flou)).convert("RGBA")


def remplacer_images(racine):
    fait = []

    def p(rel):
        # Le noyau s'appelle « ntos » dans les sources récentes, « ntoskrnl » avant
        chemin = os.path.join(racine, rel)
        if rel.startswith("ntos/") and not os.path.exists(chemin):
            chemin = os.path.join(racine, "ntoskrnl/" + rel[5:])
        return chemin

    def taille(rel):
        return Image.open(p(rel)).size

    # Écran de démarrage (palette 16 couleurs) et logo UEFI
    rel = "ntos/inbv/resources/logo.bmp"
    if os.path.exists(p(rel)):
        w, h = taille(rel)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}"/>'
               + ID.logo_groupe(w * 0.18, h * 0.06, w * 0.64)
               + f'<text x="{w / 2}" y="{h * 0.9}" text-anchor="middle" font-family="Inter Display, Inter" '
                 f'font-size="{w * 0.15:.1f}" font-weight="700" fill="#FFFFFF">Nounours'
                 f'<tspan fill="{ID.MIEL_CLAIR}">NT</tspan></text></svg>')
        _comme(p(rel), _rendu(svg, w, h))
        fait.append(rel)
    for rel, fond in (("ntos/inbv/resources/reactos_logo.bmp", NUIT),):
        if os.path.exists(p(rel)):
            w, h = taille(rel)
            _comme(p(rel), _rendu(_svg_marque(w, h, fond=None), w, h))
            fait.append(rel)

    # Bannières : À propos (fond clair), identification, propriétés système, installation
    for rel, fond, couleur in (("dll/win32/shell32/res/bitmaps/aboutbanner.bmp", "#F6F2EE", "#2A1B3D"),
                               ("base/system/logonui/res/123.bmp", "#2B1C40", "#FFFFFF"),
                               ("base/applications/screensavers/logon/res/0.bmp", "#000000", "#FFFFFF")):
        if os.path.exists(p(rel)):
            w, h = taille(rel)
            ratio = w / h
            svg = _svg_marque(w, h, fond=fond, couleur=couleur) if ratio > 2.2 else (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="{fond}"/>'
                + ID.logo_groupe(w / 2 - h * 0.3, h * 0.08, h * 0.6)
                + f'<text x="{w / 2}" y="{h * 0.88}" text-anchor="middle" font-family="Inter Display, Inter" '
                  f'font-size="{h * 0.17:.1f}" font-weight="700" fill="{couleur}">Nounours'
                  f'<tspan fill="{ID.MIEL_CLAIR}">NT</tspan></text></svg>')
            _comme(p(rel), _rendu(svg, w, h))
            fait.append(rel)

    # Logo + masque (propriétés système, première ouverture de session, installation)
    for dossier in ("dll/cpl/sysdm/resources", "base/system/userinit/res"):
        rel, relm = f"{dossier}/rosbitmap.bmp", f"{dossier}/rosbitmap_mask.bmp"
        if os.path.exists(p(rel)):
            w, h = taille(rel)
            im = _rendu(_svg_marque(w, h, texte=True, couleur="#FFFFFF", logo=h * 0.55, taille_txt=h * 0.3), w, h)
            _comme(p(rel), im)
            fait.append(rel)
            if os.path.exists(p(relm)):
                _comme(p(relm), _masque(im))
                fait.append(relm)

    rel = "base/setup/libernt/res/watermark.bmp"
    if os.path.exists(p(rel)):
        w, h = taille(rel)
        _comme(p(rel), _rendu(_svg_marque(w, h, fond=NUIT, texte=False, logo=w * 0.62), w, h))
        fait.append(rel)

    # Bouton Démarrer et icônes du système
    for rel, assombrir in (("media/graphics/start-button/default.png", False),
                           ("media/graphics/start-button/pressed.png", True)):
        if os.path.exists(p(rel)):
            w, h = taille(rel)
            im = _rendu(_svg_marque(w, h, texte=False, logo=w * 0.8), w, h)
            if assombrir:
                im = Image.composite(Image.blend(im, Image.new("RGBA", im.size, (0, 0, 0, 255)), 0.18), im, im)
            _comme(p(rel), im)
            fait.append(rel)
    rel = "base/shell/explorer/res/bmp/143.bmp"
    if os.path.exists(p(rel)):
        w, h = taille(rel)
        _comme(p(rel), _rendu(_svg_marque(w, h, fond="#000000", texte=False), w, h))
        fait.append(rel)
    for rel in ("image/data/icon.ico", "base/shell/explorer/res/ico/258.ico", "base/shell/progman/res/roslogo.ico"):
        if os.path.exists(p(rel)):
            _comme(p(rel), _rendu(ID.logo_svg(), 256, 256))
            fait.append(rel)

    # Logo du menu de démarrage, intégré au chargeur : 48 x 42, RGBA prémultiplié, brut
    rel = "bootloader/gui/assets/logo.rgba"
    if os.path.exists(p(rel)) and os.path.getsize(p(rel)) == 48 * 42 * 4:
        k = 42
        im = _rendu(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 42" width="48" height="42">'
                    f'{ID.logo_groupe((48 - k) / 2, 0, k)}</svg>', 48, 42)
        octets = bytearray()
        for r, g, b, a in im.getdata():
            octets += bytes((r * a // 255, g * a // 255, b * a // 255, a))
        with open(p(rel), "wb") as f:
            f.write(octets)
        fait.append(rel)

    # Fichiers de marque du dépôt et bannières SVG
    for rel, fond in (("media/graphics/branding/libernt-logo.png", None),
                      ("media/graphics/branding/libernt-banner.png", "#FFFFFF")):
        if os.path.exists(p(rel)):
            w, h = taille(rel)
            _comme(p(rel), _rendu(_svg_marque(w, h, fond=fond, couleur="#2A1B3D" if fond else "#FFFFFF"), w, h))
            fait.append(rel)
    if os.path.exists(p("media/graphics/branding/libernt-mark.svg")):
        with open(p("media/graphics/branding/libernt-mark.svg"), "w") as f:
            f.write(ID.logo_svg())
        fait.append("media/graphics/branding/libernt-mark.svg")
    for rel, vertical in (("dll/cpl/sysdm/resources/reactos-banner.svg", False),
                          ("media/graphics/start_menu_banner.svg", True)):
        if os.path.exists(p(rel)):
            m = re.search(r'viewBox="([\d.\s-]+)"', open(p(rel)).read())
            _x, _y, w, h = (float(v) for v in m.group(1).split()) if m else (0, 0, 300, 80)
            fond = None
            if vertical:
                fond = "#2B1C40"
            with open(p(rel), "w") as f:
                f.write(_svg_marque(w, h, fond=fond, couleur="#FFFFFF" if vertical else "#2A1B3D",
                                    vertical=vertical, taille_txt=(w * 0.45 if vertical else None)))
            fait.append(rel)
    return fait


# --- 3. Mention -------------------------------------------------------------------------
NOTICE = """NounoursNT
==========

NounoursNT est un système d'exploitation de NounoursCorp, basé sur les sources de
LiberNT (https://github.com/LiberNT/LiberNT), elles-mêmes issues de ReactOS.
Il est distribué sous la licence GNU GPL 3.0 ; le code repris garde sa licence
d'origine (le plus souvent GPL 2.0 ou ultérieure).

NounoursNT n'est ni LiberNT, ni un produit du projet LiberNT : le nom et le logo de
LiberNT ont été retirés, conformément à sa politique de marque. Les noms LiberNT,
ReactOS et Windows appartiennent à leurs propriétaires respectifs.
"""


def main():
    if len(sys.argv) != 2 or not any(os.path.isdir(os.path.join(sys.argv[1], d)) for d in ("ntos", "ntoskrnl")):
        print(__doc__)
        return 2
    racine = sys.argv[1]
    print("Textes :", renommer_textes(racine))
    manque = renommer_explicites(racine)
    if manque:
        print("⚠ Introuvables (le code de LiberNT a changé ?) :", "; ".join(manque))
    imgs = remplacer_images(racine)
    print(f"Images ({len(imgs)}) :", ", ".join(imgs))
    with open(os.path.join(racine, "NOUNOURSNT.md"), "w") as f:
        f.write(NOTICE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
