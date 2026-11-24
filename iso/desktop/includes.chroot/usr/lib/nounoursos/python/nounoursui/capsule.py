"""Capsule temporelle NounoursOS : sauvegardes automatiques du dossier personnel.

Façon Time Machine : un instantané par heure sur un disque externe (ou un dossier),
chaque instantané est un dossier complet et lisible (on y navigue avec Dolphin), mais
les fichiers inchangés ne prennent pas de place (liens durs, rsync --link-dest).
Conservation : tout sur 24 h, un par jour sur 30 jours, un par semaine ensuite ;
les plus anciens partent d'abord quand le disque se remplit.

N'importe pas Qt : utilisable par le service (nounoursos-capsule) comme par Paramètres.
"""
import fcntl
import json
import os
import re
import shutil
import socket
import subprocess
import time

CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "nounoursos")
CACHE_DIR = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "nounoursos")
CONF = os.path.join(CONFIG_DIR, "capsule.conf")
ETAT = os.path.join(CACHE_DIR, "capsule.json")
NOM_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}$")
ESPACE_MINI = 0.08          # on garde au moins 8 % du disque libre

# Ce qui ne mérite pas d'être sauvegardé (caches, corbeille, machines virtuelles…)
EXCLUSIONS = [
    ".cache/", ".local/share/Trash/", ".thumbnails/", ".local/share/baloo/",
    ".var/app/*/cache/", ".mozilla/firefox/*/cache2/", "*.part", "*.crdownload",
    ".local/share/Steam/steamapps/", ".steam/", ".winboat/", ".local/share/containers/",
    ".local/share/gnome-boxes/", "VirtualBox VMs/", ".xsession-errors*", ".nv/",
]


# --- Réglages ---------------------------------------------------------------------
def lire_conf():
    conf = {"active": "false", "destination": ""}
    try:
        with open(CONF) as f:
            for line in f:
                if "=" in line and not line.lstrip().startswith(("#", "[")):
                    k, v = line.split("=", 1)
                    conf[k.strip()] = v.strip()
    except OSError:
        pass
    return conf


def ecrire_conf(**valeurs):
    conf = lire_conf()
    conf.update({k: str(v) for k, v in valeurs.items()})
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONF, "w") as f:
        f.write("[main]\n" + "".join(f"{k} = {v}\n" for k, v in conf.items()))


def lire_etat():
    try:
        with open(ETAT) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _ecrire_etat(**valeurs):
    etat = lire_etat()
    etat.update(valeurs)
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(ETAT, "w") as f:
        json.dump(etat, f)


# --- Emplacements -------------------------------------------------------------------
def dossier_capsule(destination):
    """<destination>/NounoursOS-Capsule/<machine>-<utilisateur>"""
    user = os.environ.get("USER") or os.path.basename(os.path.expanduser("~"))
    return os.path.join(destination, "NounoursOS-Capsule", f"{socket.gethostname()}-{user}")


def disques_externes():
    """Disques branchés où l'on peut écrire : [(nom, chemin, libre, total)]."""
    user = os.environ.get("USER", "")
    vus, out = set(), []
    for base in (f"/media/{user}", f"/run/media/{user}", "/media", "/mnt"):
        try:
            noms = sorted(os.listdir(base))
        except OSError:
            continue
        for nom in noms:
            chemin = os.path.join(base, nom)
            if chemin in vus or not os.path.ismount(chemin) or not os.access(chemin, os.W_OK):
                continue
            vus.add(chemin)
            du = shutil.disk_usage(chemin)
            out.append((nom, chemin, du.free, du.total))
    return out


def liens_durs_possibles(dossier):
    """Les systèmes FAT/exFAT n'ont pas de liens durs : chaque sauvegarde serait complète."""
    a, b = os.path.join(dossier, ".test-lien"), os.path.join(dossier, ".test-lien-2")
    try:
        with open(a, "w") as f:
            f.write("ourson")
        os.link(a, b)
        return True
    except OSError:
        return False
    finally:
        for p in (a, b):
            try:
                os.unlink(p)
            except OSError:
                pass


# --- Instantanés ---------------------------------------------------------------------
def liste(destination=None):
    """Instantanés terminés, du plus récent au plus ancien : [(horodatage, chemin)]."""
    destination = destination or lire_conf().get("destination")
    if not destination:
        return []
    base = dossier_capsule(destination)
    try:
        noms = [n for n in os.listdir(base) if NOM_RE.match(n)]
    except OSError:
        return []
    out = []
    for n in sorted(noms, reverse=True):
        try:
            t = time.mktime(time.strptime(n, "%Y-%m-%d-%H%M%S"))
        except ValueError:
            continue
        out.append((t, os.path.join(base, n)))
    return out


def a_garder(horodatages, maintenant=None):
    """Règle Time Machine : tout < 24 h, 1 par jour < 30 j, 1 par semaine au-delà."""
    maintenant = maintenant or time.time()
    garde, vus = set(), set()
    for t in sorted(horodatages, reverse=True):
        age = maintenant - t
        if age < 86400:
            garde.add(t)
            continue
        cle = ("j", time.strftime("%Y-%m-%d", time.localtime(t))) if age < 30 * 86400 \
            else ("s", time.strftime("%G-%V", time.localtime(t)))
        if cle not in vus:
            vus.add(cle)
            garde.add(t)
    return garde


def elaguer(destination, journal=print):
    snaps = liste(destination)
    if len(snaps) <= 1:
        return
    garde = a_garder([t for t, _ in snaps])
    for t, chemin in snaps[1:]:              # le plus récent n'est jamais supprimé
        if t not in garde:
            journal(f"Ancien instantané supprimé : {os.path.basename(chemin)}")
            shutil.rmtree(chemin, ignore_errors=True)
    # Disque presque plein : on retire les plus anciens
    snaps = liste(destination)
    while len(snaps) > 1:
        du = shutil.disk_usage(destination)
        if du.free / du.total >= ESPACE_MINI:
            break
        journal(f"Disque presque plein : suppression de {os.path.basename(snaps[-1][1])}")
        shutil.rmtree(snaps[-1][1], ignore_errors=True)
        snaps = liste(destination)


def sauvegarder(progression=None, auto=False, journal=print):
    """Crée un instantané. Renvoie (ok, message)."""
    conf = lire_conf()
    destination = conf.get("destination", "")
    if auto and conf.get("active") != "true":
        return True, "Capsule temporelle désactivée."
    if not destination:
        return False, "Choisissez d'abord où sauvegarder."
    if not os.path.isdir(destination):
        msg = "Le disque de sauvegarde n'est pas branché."
        if not auto:
            _ecrire_etat(dernier_essai=time.time(), ok=False, message=msg)
        return (auto, msg)                  # en automatique : pas une erreur, on réessaiera
    if not shutil.which("rsync"):
        return False, "rsync est introuvable."
    base = dossier_capsule(destination)
    os.makedirs(base, exist_ok=True)
    verrou = open(os.path.join(base, ".verrou"), "w")
    try:
        fcntl.flock(verrou, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False, "Une sauvegarde est déjà en cours."

    nom = time.strftime("%Y-%m-%d-%H%M%S")
    tmp = os.path.join(base, ".en-cours")
    precedents = liste(destination)
    home = os.path.expanduser("~").rstrip("/") + "/"
    cmd = ["rsync", "-a", "--delete", "--delete-excluded", "--info=progress2", "--no-inc-recursive",
           "--partial", "--one-file-system"]
    for ex in EXCLUSIONS:
        cmd += ["--exclude", "/" + ex]
    # Ne jamais se sauvegarder soi-même si la destination est dans le dossier personnel
    dest_abs = os.path.realpath(destination) + "/"
    if dest_abs.startswith(home):
        cmd += ["--exclude", "/" + dest_abs[len(home):]]
    if precedents and liens_durs_possibles(base):
        cmd += ["--link-dest", precedents[0][1]]
    cmd += [home, tmp + "/"]

    _ecrire_etat(en_cours=True, debut=time.time())
    journal("Sauvegarde vers " + base)
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                             env={**os.environ, "LC_ALL": "C"}, bufsize=1)
        if progression:
            for ligne in iter(lambda: p.stdout.readline() or None, None):
                m = re.search(r"(\d+)%", ligne)
                if m:
                    progression(int(m.group(1)))
        else:
            p.stdout.read()
        err = p.stderr.read()
        rc = p.wait()
    finally:
        _ecrire_etat(en_cours=False)
    # 24 = des fichiers ont disparu pendant la copie : normal sur un système vivant
    if rc not in (0, 24):
        msg = "La sauvegarde a échoué : " + (err.strip().splitlines() or ["erreur inconnue"])[-1]
        _ecrire_etat(dernier_essai=time.time(), ok=False, message=msg)
        return False, msg
    os.rename(tmp, os.path.join(base, nom))
    try:
        os.utime(os.path.join(base, nom))
    except OSError:
        pass
    elaguer(destination, journal)
    _ecrire_etat(derniere=time.time(), dernier_essai=time.time(), ok=True, message="")
    return True, "Sauvegarde terminée."


def restaurer(instantane, dossier_cible, progression=None):
    """Copie un instantané (ou une partie) dans dossier_cible, sans rien écraser d'autre."""
    os.makedirs(dossier_cible, exist_ok=True)
    cmd = ["rsync", "-a", "--info=progress2", "--no-inc-recursive",
           instantane.rstrip("/") + "/", dossier_cible.rstrip("/") + "/"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for ligne in p.stdout:
        m = re.search(r"(\d+)%", ligne)
        if m and progression:
            progression(int(m.group(1)))
    return p.wait() in (0, 24)


def libelle(t):
    """« Aujourd'hui à 14:00 », « Hier à 09:00 », « 3 mars à 18:00 »."""
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
            "septembre", "octobre", "novembre", "décembre"]
    lt, maintenant = time.localtime(t), time.localtime()
    heure = time.strftime("%H:%M", lt)
    jours = (time.mktime(time.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d"))
             - time.mktime(time.strptime(time.strftime("%Y-%m-%d", lt), "%Y-%m-%d"))) / 86400
    if jours < 1:
        return f"Aujourd'hui à {heure}"
    if jours < 2:
        return f"Hier à {heure}"
    annee = "" if lt.tm_year == maintenant.tm_year else f" {lt.tm_year}"
    return f"{lt.tm_mday} {mois[lt.tm_mon - 1]}{annee} à {heure}"
