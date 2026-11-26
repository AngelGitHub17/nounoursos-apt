"""Serveur Minecraft en 1 clic (Paper), pour le bureau comme pour NounoursOS Server.

- Paper téléchargé depuis l'API officielle Fill v3 (empreinte SHA-256 vérifiée)
- Java choisi selon ce que demande la version (21 ou 25, paquets Debian)
- Service systemd de l'utilisateur ; console par RCON (mot de passe aléatoire, local)
- Sauvegardes du monde dans ~/Minecraft/Sauvegardes (les 7 dernières)
N'importe pas Qt.
"""
import glob
import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import struct
import subprocess
import tarfile
import time
import urllib.request

API = os.environ.get("NOUNOURSOS_PAPER_API", "https://fill.papermc.io/v3/projects/paper")
UA = "NounoursOS (https://nounourscorp.fr/)"
# Mode système (NounoursOS Server) : compte « minecraft », dossier /srv/minecraft, service systemd du système
SYSTEME = os.environ.get("NOUNOURSOS_MINECRAFT_SYSTEME") == "1"
COMPTE = "minecraft"
BASE = os.environ.get("NOUNOURSOS_MINECRAFT", "/srv/minecraft" if SYSTEME else os.path.expanduser("~/Minecraft"))
DOSSIER = os.path.join(BASE, "Serveur")
SAUVEGARDES = os.path.join(BASE, "Sauvegardes")
CONF = os.path.join(DOSSIER, "nounoursos.json")
SERVICE = "nounoursos-minecraft.service"
CLUF = "https://aka.ms/MinecraftEULA"
GARDER = 7


class ErreurMinecraft(Exception):
    pass


# --- API Paper ----------------------------------------------------------------------
def _get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except (OSError, ValueError) as e:
        raise ErreurMinecraft(f"Impossible de joindre PaperMC ({e}).")


def versions():
    """Versions publiées, de la plus récente à la plus ancienne (sans les préversions)."""
    d = _get(API)
    res = []
    for groupe in d.get("versions", {}).values():
        res += [v for v in groupe if re.fullmatch(r"[\d.]+", v)]
    cle = lambda v: [int(x) for x in v.split(".")]
    return sorted(set(res), key=cle, reverse=True)


def infos_version(version):
    """{java, support, build, nom, url, sha256, taille, drapeaux}"""
    v = _get(f"{API}/versions/{version}").get("version", {})
    builds = _get(f"{API}/versions/{version}/builds")
    stables = [b for b in builds if b.get("channel") == "STABLE"] or builds
    if not stables:
        raise ErreurMinecraft(f"Aucune version de Paper disponible pour Minecraft {version}.")
    b = stables[0]
    dl = b["downloads"]["server:default"]
    return {"version": version, "java": v.get("java", {}).get("version", {}).get("minimum", 21),
            "support": v.get("support", {}).get("status", ""), "build": b["id"], "nom": dl["name"],
            "url": dl["url"], "sha256": dl["checksums"]["sha256"], "taille": dl.get("size", 0),
            "drapeaux": v.get("java", {}).get("flags", {}).get("recommended", [])}


# --- Java -----------------------------------------------------------------------------
def java_pour(minimum):
    """Chemin d'un Java installé ≥ minimum (le plus proche), sinon None."""
    trouves = []
    for chemin in glob.glob("/usr/lib/jvm/java-*-openjdk-*/bin/java"):
        m = re.search(r"java-(\d+)-openjdk", chemin)
        if m and int(m.group(1)) >= int(minimum):
            trouves.append((int(m.group(1)), chemin))
    return sorted(trouves)[0][1] if trouves else None


def paquet_java(minimum):
    for n in (21, 25):
        if n >= int(minimum):
            return n
    return None


# --- Configuration -------------------------------------------------------------------
def lire():
    try:
        with open(CONF, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def ecrire(conf):
    os.makedirs(DOSSIER, exist_ok=True)
    with open(CONF + ".tmp", "w", encoding="utf-8") as f:
        json.dump(conf, f, indent=2, ensure_ascii=False)
    os.replace(CONF + ".tmp", CONF)


def installe():
    c = lire()
    return bool(c.get("jar")) and os.path.exists(os.path.join(DOSSIER, c["jar"]))


def memoire_conseillee():
    try:
        total = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2 ** 30
    except (ValueError, OSError):
        total = 8
    return 2 if total < 6 else 4 if total < 12 else 6


def proprietes(chemin=None):
    chemin = chemin or os.path.join(DOSSIER, "server.properties")
    res = {}
    try:
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                if "=" in ligne and not ligne.startswith("#"):
                    k, v = ligne.rstrip("\n").split("=", 1)
                    res[k] = v
    except OSError:
        pass
    return res


def regler_proprietes(valeurs):
    chemin = os.path.join(DOSSIER, "server.properties")
    lignes, vus = [], set()
    try:
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                k = ligne.split("=", 1)[0]
                if "=" in ligne and not ligne.startswith("#") and k in valeurs:
                    lignes.append(f"{k}={valeurs[k]}\n")
                    vus.add(k)
                else:
                    lignes.append(ligne)
    except OSError:
        pass
    lignes += [f"{k}={v}\n" for k, v in valeurs.items() if k not in vus]
    with open(chemin, "w", encoding="utf-8") as f:
        f.writelines(lignes)


# --- Installation ---------------------------------------------------------------------
def telecharger(info, progression=None):
    os.makedirs(DOSSIER, exist_ok=True)
    final = os.path.join(DOSSIER, info["nom"])
    part = final + ".part"
    req = urllib.request.Request(info["url"], headers={"User-Agent": UA})
    h = hashlib.sha256()
    try:
        with urllib.request.urlopen(req, timeout=60) as r, open(part, "wb") as f:
            total = int(r.headers.get("Content-Length") or info.get("taille") or 0)
            recu, dernier = 0, -1
            while True:
                bloc = r.read(1 << 16)
                if not bloc:
                    break
                f.write(bloc)
                h.update(bloc)
                recu += len(bloc)
                if progression and total and int(recu * 100 / total) != dernier:
                    dernier = int(recu * 100 / total)
                    progression(dernier)
    except OSError as e:
        raise ErreurMinecraft(f"Téléchargement interrompu ({e}).")
    if h.hexdigest() != info["sha256"]:
        os.unlink(part)
        raise ErreurMinecraft("Le fichier téléchargé est abîmé (empreinte SHA-256 différente). Réessayez.")
    os.replace(part, final)
    return info["nom"]


def installer(info, accepte_cluf, memoire=None, nom="Serveur NounoursOS", progression=None):
    """Télécharge Paper et prépare le dossier. Le CLUF doit avoir été accepté par l'utilisateur."""
    if not accepte_cluf:
        raise ErreurMinecraft("Il faut accepter le contrat de licence (CLUF) de Minecraft.")
    if not java_pour(info["java"]):
        n = paquet_java(info["java"])
        if SYSTEME and os.geteuid() == 0 and n:
            subprocess.run(["apt-get", "install", "-y", f"openjdk-{n}-jre-headless"], check=False,
                           env=dict(os.environ, DEBIAN_FRONTEND="noninteractive"))
        if not java_pour(info["java"]):
            raise ErreurMinecraft(f"Java {n} n'est pas installé.")
    if SYSTEME:
        preparer_compte()
    ancien = lire()
    jar = telecharger(info, progression)
    if ancien.get("jar") and ancien["jar"] != jar:
        try:
            os.unlink(os.path.join(DOSSIER, ancien["jar"]))
        except OSError:
            pass
    with open(os.path.join(DOSSIER, "eula.txt"), "w") as f:
        f.write(f"# Accepté par l'utilisateur dans NounoursOS ({CLUF})\neula=true\n")
    p = proprietes()
    valeurs = {"enable-rcon": "true", "rcon.port": p.get("rcon.port", "25575"),
               "rcon.password": p.get("rcon.password") or secrets.token_urlsafe(18),
               "broadcast-rcon-to-ops": "false"}
    if "motd" not in p:
        valeurs["motd"] = nom
    regler_proprietes(valeurs)
    conf = dict(ancien, version=info["version"], build=info["build"], jar=jar, java=info["java"],
                drapeaux=info["drapeaux"], memoire=memoire or ancien.get("memoire") or memoire_conseillee())
    ecrire(conf)
    ecrire_service()
    return conf


def _chemin_service():
    if SYSTEME:
        return f"/etc/systemd/system/{SERVICE}"
    return os.path.expanduser(f"~/.config/systemd/user/{SERVICE}")


def preparer_compte():
    """Mode système : compte « minecraft » sans connexion, propriétaire de /srv/minecraft."""
    import pwd
    try:
        pwd.getpwnam(COMPTE)
    except KeyError:
        subprocess.run(["useradd", "--system", "--home-dir", BASE, "--shell", "/usr/sbin/nologin", COMPTE],
                       check=True)
    os.makedirs(DOSSIER, exist_ok=True)
    os.makedirs(SAUVEGARDES, exist_ok=True)


def _proprietaire():
    if SYSTEME:
        subprocess.run(["chown", "-R", f"{COMPTE}:{COMPTE}", BASE], capture_output=True)


def ecrire_service():
    c = lire()
    java = java_pour(c.get("java", 21)) or "/usr/bin/java"
    mem = int(c.get("memoire", 4))
    args = " ".join([f"-Xms{mem}G", f"-Xmx{mem}G"] + c.get("drapeaux", []) +
                    ["-jar", c["jar"], "--nogui"])
    os.makedirs(os.path.dirname(_chemin_service()), exist_ok=True)
    compte = f"User={COMPTE}\nGroup={COMPTE}\n" if SYSTEME else ""
    cible = "multi-user.target" if SYSTEME else "default.target"
    with open(_chemin_service(), "w") as f:
        f.write(f"""[Unit]
Description=Serveur Minecraft NounoursOS (Paper {c.get('version', '')})
After=network-online.target
Wants=network-online.target

[Service]
{compte}WorkingDirectory={DOSSIER}
ExecStart={java} {args}
Restart=on-failure
RestartSec=10
TimeoutStopSec=120
Nice=2

[Install]
WantedBy={cible}
""")
    _proprietaire()
    _sc("daemon-reload")


# --- Service --------------------------------------------------------------------------
def _sc(*args):
    base = ["systemctl"] if SYSTEME else ["systemctl", "--user"]
    return subprocess.run(base + list(args), capture_output=True, text=True, timeout=120)


def etat():
    r = _sc("is-active", SERVICE).stdout.strip()
    return r or "inactive"          # active, activating, inactive, failed


def demarrer():
    r = _sc("start", SERVICE)
    if r.returncode:
        raise ErreurMinecraft(r.stderr.strip() or "Démarrage impossible.")


def arreter():
    _sc("stop", SERVICE)


def au_demarrage(on):
    _sc("enable" if on else "disable", SERVICE)


def au_demarrage_actif():
    return _sc("is-enabled", SERVICE).stdout.strip() == "enabled"


def journal(lignes=200):
    try:
        with open(os.path.join(DOSSIER, "logs", "latest.log"), encoding="utf-8", errors="replace") as f:
            return f.readlines()[-lignes:]
    except OSError:
        return []


def adresses():
    p = proprietes()
    port = p.get("server-port", "25565")
    ips = []
    try:
        out = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=5).stdout.split()
        ips = [i for i in out if ":" not in i]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return [f"{ip}:{port}" if port != "25565" else ip for ip in ips]


# --- RCON -----------------------------------------------------------------------------
def rcon(commande, timeout=5):
    p = proprietes()
    if p.get("enable-rcon") != "true" or not p.get("rcon.password"):
        raise ErreurMinecraft("Console indisponible (RCON désactivé).")
    try:
        s = socket.create_connection(("127.0.0.1", int(p.get("rcon.port", 25575))), timeout=timeout)
    except OSError:
        raise ErreurMinecraft("Le serveur n'est pas encore prêt.")

    def envoyer(i, t, corps):
        data = struct.pack("<ii", i, t) + corps.encode("utf-8") + b"\x00\x00"
        s.sendall(struct.pack("<i", len(data)) + data)

    def recevoir():
        n = struct.unpack("<i", _lire(s, 4))[0]
        data = _lire(s, n)
        i, t = struct.unpack("<ii", data[:8])
        return i, data[8:-2].decode("utf-8", "replace")
    try:
        envoyer(1, 3, p["rcon.password"])
        if recevoir()[0] == -1:
            raise ErreurMinecraft("Mot de passe RCON refusé.")
        envoyer(2, 2, commande)
        return re.sub(r"§.", "", recevoir()[1])
    finally:
        s.close()


def _lire(s, n):
    buf = b""
    while len(buf) < n:
        b = s.recv(n - len(buf))
        if not b:
            raise ErreurMinecraft("Connexion à la console perdue.")
        buf += b
    return buf


def joueurs():
    """(connectés, maximum, [noms]) ou None."""
    try:
        r = rcon("list")
    except ErreurMinecraft:
        return None
    m = re.search(r"(\d+)\D+(\d+)[^:]*:\s*(.*)", r)
    if not m:
        return None
    noms = [n.strip() for n in m.group(3).split(",") if n.strip()]
    return int(m.group(1)), int(m.group(2)), noms


# --- Sauvegardes ----------------------------------------------------------------------
def mondes():
    nom = proprietes().get("level-name", "world")
    return [d for d in (nom, nom + "_nether", nom + "_the_end") if os.path.isdir(os.path.join(DOSSIER, d))]


def sauvegarder():
    os.makedirs(SAUVEGARDES, exist_ok=True)
    en_marche = etat() == "active"
    if en_marche:
        try:
            rcon("save-off")
            rcon("save-all flush", timeout=60)
        except ErreurMinecraft:
            en_marche = False
    try:
        chemin = os.path.join(SAUVEGARDES, time.strftime("monde-%Y-%m-%d-%Hh%M.tar.gz"))
        with tarfile.open(chemin + ".part", "w:gz") as t:
            for d in mondes():
                t.add(os.path.join(DOSSIER, d), arcname=d,
                      filter=lambda i: None if i.name.endswith("session.lock") else i)
        os.replace(chemin + ".part", chemin)
        _proprietaire()
    finally:
        if en_marche:
            try:
                rcon("save-on")
            except ErreurMinecraft:
                pass
    for vieux in sauvegardes()[GARDER:]:
        os.unlink(vieux)
    return chemin


def sauvegardes():
    return sorted(glob.glob(os.path.join(SAUVEGARDES, "monde-*.tar.gz")), reverse=True)


def supprimer_serveur():
    """Garde les sauvegardes ; supprime le serveur et son service."""
    arreter()
    au_demarrage(False)
    try:
        os.unlink(_chemin_service())
    except OSError:
        pass
    _sc("daemon-reload")
    shutil.rmtree(DOSSIER, ignore_errors=True)
