"""Migration depuis Windows : récupérer ses fichiers et ses favoris.

Le disque Windows est ouvert en LECTURE SEULE (udisksctl) : rien n'y est modifié.
Les fichiers sont copiés sans jamais écraser un fichier existant de NounoursOS.
Les favoris d'Edge, Chrome et Firefox sont rassemblés dans un fichier HTML importable
par n'importe quel navigateur. N'importe pas Qt.
"""
import html
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time

# Dossier Windows → dossier XDG de NounoursOS
DOSSIERS = [
    ("Documents", "DOCUMENTS", "Documents"),
    ("Pictures", "PICTURES", "Images"),
    ("Music", "MUSIC", "Musique"),
    ("Videos", "VIDEOS", "Vidéos"),
    ("Desktop", "DESKTOP", "Bureau"),
    ("Downloads", "DOWNLOAD", "Téléchargements"),
]
IGNORES = {"Default", "Default User", "All Users", "Public", "defaultuser0", "WDAGUtilityAccount"}


# --- Disques ------------------------------------------------------------------------
def disques_windows():
    """Partitions Windows : [{chemin, nom, taille, montage, bitlocker}]."""
    try:
        out = subprocess.run(["lsblk", "-J", "-b", "-o", "NAME,PATH,FSTYPE,LABEL,SIZE,MOUNTPOINTS"],
                             capture_output=True, text=True, timeout=10).stdout
        arbre = json.loads(out or "{}").get("blockdevices", [])
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []
    res = []

    def parcourir(noeuds):
        for n in noeuds:
            fs = (n.get("fstype") or "").lower()
            if fs in ("ntfs", "ntfs3", "bitlocker"):
                montages = [m for m in (n.get("mountpoints") or []) if m]
                res.append({"chemin": n.get("path"), "nom": n.get("label") or n.get("name"),
                            "taille": int(n.get("size") or 0), "montage": montages[0] if montages else None,
                            "bitlocker": fs == "bitlocker"})
            parcourir(n.get("children") or [])
    parcourir(arbre)
    return res


def monter(chemin):
    """Ouvre la partition en lecture seule ; renvoie le point de montage."""
    r = subprocess.run(["udisksctl", "mount", "--no-user-interaction", "-b", chemin, "-o", "ro"],
                       capture_output=True, text=True, timeout=60)
    m = re.search(r" at (.+?)\.?$", r.stdout.strip())
    if r.returncode == 0 and m:
        return m.group(1)
    if "AlreadyMounted" in r.stderr:
        m = re.search(r"mounted at [`'](.+?)[`']", r.stderr)
        if m:
            return m.group(1)
    if "hibernat" in r.stderr.lower() or "unclean" in r.stderr.lower():
        raise RuntimeError("Windows n'a pas été complètement arrêté (démarrage rapide). Dans Windows : "
                           "Maj + clic sur Arrêter, puis réessayez.")
    raise RuntimeError(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "Ouverture impossible.")


def demonter(chemin):
    subprocess.run(["udisksctl", "unmount", "--no-user-interaction", "-b", chemin],
                   capture_output=True, timeout=30)


# --- Comptes et contenu ---------------------------------------------------------------
def comptes(racine):
    """Comptes Windows présents sur la partition : [nom]."""
    users = os.path.join(racine, "Users")
    try:
        noms = sorted(os.listdir(users), key=str.lower)
    except OSError:
        return []
    return [n for n in noms if n not in IGNORES and not n.startswith(".")
            and os.path.isdir(os.path.join(users, n))
            and (os.path.exists(os.path.join(users, n, "NTUSER.DAT"))
                 or os.path.isdir(os.path.join(users, n, "Documents")))]


def taille_dossier(chemin, limite_s=8):
    total, debut = 0, time.time()
    for racine, _d, fichiers in os.walk(chemin):
        for f in fichiers:
            try:
                total += os.lstat(os.path.join(racine, f)).st_size
            except OSError:
                pass
        if time.time() - debut > limite_s:      # très gros dossier : estimation suffisante
            return total, False
    return total, True


def dossier_xdg(cle, defaut):
    try:
        d = subprocess.run(["xdg-user-dir", cle], capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        d = ""
    if not d or d == os.path.expanduser("~"):
        d = os.path.join(os.path.expanduser("~"), defaut)
    return d


def elements(racine, compte):
    """Ce qu'on peut récupérer : [{cle, titre, source, cible, taille, exacte}]."""
    base = os.path.join(racine, "Users", compte)
    res = []
    for win, xdg, fr in DOSSIERS:
        src = os.path.join(base, win)
        if os.path.isdir(src):
            t, exacte = taille_dossier(src)
            res.append({"cle": win, "titre": fr, "source": src, "cible": dossier_xdg(xdg, fr),
                        "taille": t, "exacte": exacte})
    onedrive = next((os.path.join(base, d) for d in sorted(os.listdir(base)) if d.startswith("OneDrive")
                     and os.path.isdir(os.path.join(base, d))), None) if os.path.isdir(base) else None
    if onedrive:
        t, exacte = taille_dossier(onedrive)
        res.append({"cle": "OneDrive", "titre": "OneDrive (fichiers présents sur le disque)", "source": onedrive,
                    "cible": os.path.join(os.path.expanduser("~"), "OneDrive"), "taille": t, "exacte": exacte})
    fav = favoris(racine, compte)
    if fav:
        res.append({"cle": "favoris", "titre": f"Favoris des navigateurs ({len(fav)})", "source": None,
                    "cible": os.path.join(dossier_xdg("DOCUMENTS", "Documents"),
                                          "Favoris importés de Windows.html"),
                    "taille": 0, "exacte": True, "favoris": fav})
    return res


# --- Favoris --------------------------------------------------------------------------
def _chromium(fichier, navigateur):
    try:
        with open(fichier, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return []
    out = []

    def parcourir(noeud, dossier):
        if noeud.get("type") == "url":
            out.append((navigateur, dossier, noeud.get("name", ""), noeud.get("url", "")))
        for enfant in noeud.get("children", []):
            parcourir(enfant, dossier if noeud.get("type") != "folder" or not noeud.get("name") else
                      (dossier + " / " if dossier else "") + noeud["name"])
    for racine in d.get("roots", {}).values():
        if isinstance(racine, dict):
            parcourir(racine, "")
    return out


def _firefox(places, navigateur="Firefox"):
    tmp = tempfile.mktemp(suffix=".sqlite")
    try:
        shutil.copy(places, tmp)                    # la base peut être verrouillée : on lit une copie
        con = sqlite3.connect(tmp)
        lignes = con.execute("SELECT b.title, p.url, (SELECT title FROM moz_bookmarks WHERE id = b.parent) "
                             "FROM moz_bookmarks b JOIN moz_places p ON p.id = b.fk "
                             "WHERE b.type = 1 AND p.url NOT LIKE 'place:%'").fetchall()
        con.close()
    except (OSError, sqlite3.Error):
        return []
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return [(navigateur, dossier or "", titre or url, url) for titre, url, dossier in lignes]


def favoris(racine, compte):
    base = os.path.join(racine, "Users", compte, "AppData")
    trouves = []
    for nom, rel in (("Edge", "Local/Microsoft/Edge/User Data"), ("Chrome", "Local/Google/Chrome/User Data"),
                     ("Brave", "Local/BraveSoftware/Brave-Browser/User Data"), ("Opera", "Roaming/Opera Software")):
        d = os.path.join(base, rel)
        if not os.path.isdir(d):
            continue
        for profil in sorted(os.listdir(d)):
            f = os.path.join(d, profil, "Bookmarks")
            if os.path.isfile(f):
                trouves += _chromium(f, nom)
        if os.path.isfile(os.path.join(d, "Opera Stable", "Bookmarks")):
            trouves += _chromium(os.path.join(d, "Opera Stable", "Bookmarks"), nom)
    profils = os.path.join(base, "Roaming/Mozilla/Firefox/Profiles")
    if os.path.isdir(profils):
        for p in sorted(os.listdir(profils)):
            f = os.path.join(profils, p, "places.sqlite")
            if os.path.isfile(f):
                trouves += _firefox(f)
    vus, uniques = set(), []
    for t in trouves:
        if t[3] and t[3] not in vus and t[3].startswith(("http://", "https://")):
            vus.add(t[3])
            uniques.append(t)
    return uniques


def ecrire_favoris(liste, chemin):
    """Format « Netscape bookmarks » : importable dans Firefox, NounoursBrowser, Chrome…"""
    par_nav = {}
    for nav, dossier, titre, url in liste:
        par_nav.setdefault(nav, {}).setdefault(dossier, []).append((titre, url))
    lignes = ["<!DOCTYPE NETSCAPE-Bookmark-file-1>", '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; '
              'charset=UTF-8">', "<TITLE>Favoris importés de Windows</TITLE>", "<H1>Favoris importés de Windows</H1>",
              "<DL><p>"]
    for nav, dossiers in par_nav.items():
        lignes.append(f"<DT><H3>{html.escape(nav)}</H3>")
        lignes.append("<DL><p>")
        for dossier, items in dossiers.items():
            if dossier:
                lignes += [f"<DT><H3>{html.escape(dossier)}</H3>", "<DL><p>"]
            for titre, url in items:
                lignes.append(f'<DT><A HREF="{html.escape(url, quote=True)}">{html.escape(titre)}</A>')
            if dossier:
                lignes.append("</DL><p>")
        lignes.append("</DL><p>")
    lignes.append("</DL><p>")
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes) + "\n")
    return chemin


# --- Copie ----------------------------------------------------------------------------
def copier(element, progression=None):
    """Copie un élément (jamais d'écrasement). Renvoie True si tout s'est bien passé."""
    if element["cle"] == "favoris":
        ecrire_favoris(element["favoris"], element["cible"])
        return True
    os.makedirs(element["cible"], exist_ok=True)
    cmd = ["rsync", "-rt", "--ignore-existing", "--info=progress2", "--no-inc-recursive",
           "--exclude", "desktop.ini", "--exclude", "Thumbs.db", "--exclude", "$RECYCLE.BIN",
           "--exclude", "My Music", "--exclude", "My Pictures", "--exclude", "My Videos",
           element["source"].rstrip("/") + "/", element["cible"].rstrip("/") + "/"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for ligne in p.stdout:
        m = re.search(r"(\d+)%", ligne)
        if m and progression:
            progression(int(m.group(1)))
    return p.wait() in (0, 23, 24)      # 23 : quelques fichiers illisibles (fichiers système), on continue
