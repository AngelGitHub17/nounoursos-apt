"""Moteur des mises à jour NounoursOS.

- Recherche : `apt-get update` via l'action « maj-rechercher » (pkexec, sans mot de passe,
  délais bornés), repli sur PackageKit ; puis `apt list --upgradable`.
- Installation : PackageKit (`pkcon update`), maintenant ou au redémarrage
  (« offline update » : téléchargement maintenant, installation au reboot).
- Les mises à jour du paquet `nounoursos-release` (dépôt NounoursCorp) sont
  présentées comme une nouvelle version de NounoursOS, façon macOS.
"""
import json
import os
import re
import time
from dataclasses import dataclass, field, asdict

from . import run, has, DEMO, CACHE_DIR, os_release

RELEASE_PKG = "nounoursos-release"
STATE_FILE = os.path.join(CACHE_DIR, "maj.json")

# Paquets dont la mise à jour justifie un redémarrage
REBOOT_HINTS = ("linux-image", "systemd", "libc6", "dbus", "kwin", "plasma-workspace",
                "nvidia", "firmware-", "intel-microcode", "amd64-microcode", "sddm")


@dataclass
class Update:
    name: str
    new: str
    old: str
    suite: str
    size: int = 0

    @property
    def security(self):
        return "security" in self.suite

    @property
    def nounoursos(self):
        return self.name.startswith("nounoursos")


@dataclass
class UpdateSet:
    updates: list = field(default_factory=list)
    checked_at: float = 0.0
    error: str = ""
    notes: str = ""

    @property
    def count(self):
        return len(self.updates)

    @property
    def security_count(self):
        return sum(1 for u in self.updates if u.security)

    @property
    def size(self):
        return sum(u.size for u in self.updates)

    @property
    def needs_reboot(self):
        return any(u.name.startswith(REBOOT_HINTS) for u in self.updates)

    @property
    def new_release(self):
        """Nouvelle version de NounoursOS (ex. « 1.1 ») si le dépôt en propose une."""
        for u in self.updates:
            if u.name == RELEASE_PKG:
                return u.new.split("-")[0].split("+")[0]
        return None

    def headline(self):
        rel = os_release()
        if self.new_release:
            return f"NounoursOS {self.new_release}"
        return f"Mise à jour de NounoursOS {rel.get('VERSION_ID', '')}".strip()

    def summary(self):
        parts = [f"{self.count} mise{'s' if self.count > 1 else ''} à jour"]
        if self.security_count:
            parts.append(f"dont {self.security_count} de sécurité")
        txt = " ".join(parts)
        if self.size:
            txt += " · " + human_size(self.size)
        return txt

    def signature(self):
        return "|".join(sorted(f"{u.name}={u.new}" for u in self.updates))

    def to_json(self):
        return {"checked_at": self.checked_at, "error": self.error, "notes": self.notes,
                "updates": [asdict(u) for u in self.updates]}

    @classmethod
    def from_json(cls, d):
        return cls([Update(**u) for u in d.get("updates", [])],
                   d.get("checked_at", 0.0), d.get("error", ""), d.get("notes", ""))


def human_size(n):
    for unit in ("o", "Ko", "Mo", "Go"):
        if n < 1024 or unit == "Go":
            return f"{n:.0f} {unit}" if unit in ("o", "Ko") else f"{n:.1f} {unit}".replace(".", ",")
        n /= 1024


_LINE = re.compile(r"^(\S+)/(\S+)\s+(\S+)\s+\S+\s+\[(?:upgradable from|pouvant être mis à jour depuis)\s*:\s*(\S+)\]")


RECHERCHE_ACTION = "fr.nounourscorp.nounoursos.maj-rechercher"
RECHERCHE_BIN = "/usr/libexec/nounoursos/nounoursos-maj-recherche"
RECHERCHE_LOG = os.path.join(CACHE_DIR, "recherche.log")
RECHERCHE_MAX = 330          # secondes, au-delà on abandonne


def _stream(cmd, timeout, progress):
    """Lance cmd, transmet chaque ligne à progress(), renvoie (code, sortie)."""
    import subprocess
    import threading
    lines = []
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             env={**os.environ, "LC_ALL": "C"}, bufsize=1)
    except OSError as e:
        return 127, str(e)
    killer = threading.Timer(timeout, p.kill)
    killer.start()
    try:
        for line in p.stdout:
            line = line.rstrip()
            lines.append(line)
            if progress:
                msg = _statut(line)
                if msg:
                    progress(msg)
        rc = p.wait()
    finally:
        killer.cancel()
    if rc < 0:                      # tué par le minuteur
        rc = 124
    return rc, "\n".join(lines)


def _statut(line):
    """Ligne APT/PackageKit -> message lisible (ou None)."""
    if line.startswith("dlstatus:"):
        parts = line.split(":", 3)
        try:
            return f"Téléchargement de la liste des paquets… {float(parts[2]):.0f} %"
        except (IndexError, ValueError):
            return "Téléchargement de la liste des paquets…"
    if "Waiting for cache lock" in line or "Could not get lock" in line or "lock" in line.lower() and "held" in line:
        m = re.search(r"held by process \d+ \(([^)]+)\)", line)
        return f"Un autre outil de mise à jour travaille ({m.group(1) if m else 'APT'}), attente…"
    if line.startswith(("Hit:", "Get:", "Ign:")):
        host = re.search(r"https?://([^/ ]+)", line)
        return f"Connexion à {host.group(1)}…" if host else None
    if line.startswith("Reading package lists"):
        return "Lecture de la liste des paquets…"
    if line.startswith("Status:"):
        st = line.split(":", 1)[1].strip()
        return STATUS_FR.get(st, None)
    return None


def expliquer(rc, out):
    """Message clair pour un échec de recherche."""
    if rc == 124:
        return ("La recherche a pris trop de temps (connexion lente, ou un autre outil de mise à jour "
                "bloque). Réessayez dans quelques minutes.")
    if "lock" in out and ("held" in out or "Could not get lock" in out):
        return "Un autre outil de mise à jour est en cours. Réessayez dans quelques minutes."
    if re.search(r"Temporary failure resolving|Could not resolve|Network is unreachable|"
                 r"Connection timed out|Could not connect", out):
        return "Les serveurs de mise à jour sont injoignables. Vérifiez votre connexion à Internet."
    if re.search(r"NO_PUBKEY|EXPKEYSIG|is not signed|signatures were invalid|sqv", out):
        return ("La signature d'un dépôt est invalide : la liste n'a pas été mise à jour par sécurité. "
                "Ouvrez le journal pour voir lequel.")
    if re.search(r"404\s+Not Found|does not have a Release file", out):
        return "Un dépôt de mises à jour est introuvable. Ouvrez le journal pour voir lequel."
    if "Failed to obtain authentication" in out or rc in (126, 127):
        return "Autorisation refusée pour rechercher les mises à jour."
    return "La recherche des mises à jour a échoué. Ouvrez le journal pour le détail."


def _autorise_sans_mdp():
    """Vrai si polkit autorise la recherche sans demander de mot de passe."""
    if not has("pkcheck"):
        return False
    r = run(["sh", "-c", f"pkcheck --action-id {RECHERCHE_ACTION} --process $PPID >/dev/null 2>&1; echo $?"],
            timeout=10)
    return r.strip() == "0"


def refresh(progress=None):
    """Rafraîchit la liste des paquets. Renvoie (ok, message d'erreur, journal)."""
    if DEMO:
        for m in ("Connexion à angelgithub17.github.io…", "Connexion à deb.debian.org…",
                  "Lecture de la liste des paquets…"):
            if progress:
                progress(m)
            time.sleep(0.4)
        return True, "", ""
    if has("pkexec") and os.path.exists(RECHERCHE_BIN) and _autorise_sans_mdp():
        rc, out = _stream(["pkexec", "--disable-internal-agent", RECHERCHE_BIN],
                          RECHERCHE_MAX, progress)
    elif has("pkcon"):
        rc, out = _stream(["pkcon", "refresh", "--plain", "--noninteractive"], RECHERCHE_MAX, progress)
        if rc == 0 and "Fatal" in out:
            rc = 1
    else:
        return False, "Aucun outil de mise à jour disponible.", ""
    _garder_journal(out)
    out = out.rsplit("=== essai ", 1)[-1]      # seul le dernier essai compte
    # apt-get update renvoie 0 même si un dépôt a échoué (« W: Failed to fetch ») : on le signale
    if rc == 0 and re.search(r"^(E:|W: Failed to fetch|Err:)", out, re.M):
        return False, expliquer(1, out), out
    return rc == 0, ("" if rc == 0 else expliquer(rc, out)), out


def _garder_journal(out):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(RECHERCHE_LOG, "w") as f:
            f.write(time.strftime("=== %d/%m/%Y %H:%M:%S\n") + out + "\n")
    except OSError:
        pass


def list_updates():
    if DEMO:
        return _demo()
    out = run(["env", "LC_ALL=C", "apt", "list", "--upgradable"], timeout=60)
    ups = []
    for line in out.splitlines():
        m = _LINE.match(line.strip())
        if m:
            name, suite, new, old = m.groups()
            ups.append(Update(name, new, old, suite.split(",")[0]))
    _fill_sizes(ups)
    return UpdateSet(ups, time.time())


def _fill_sizes(ups):
    if not ups:
        return
    out = run(["env", "LC_ALL=C", "apt-cache", "show", *[f"{u.name}={u.new}" for u in ups]], timeout=60)
    sizes, cur = {}, None
    for line in out.splitlines():
        if line.startswith("Package: "):
            cur = line.split(": ", 1)[1]
        elif line.startswith("Size: ") and cur and cur not in sizes:
            sizes[cur] = int(line.split(": ", 1)[1])
    for u in ups:
        u.size = sizes.get(u.name, 0)


def check(progress=None):
    """Recherche complète + mémorisation pour les autres applis (badge…)."""
    ok, erreur, _ = refresh(progress)
    if progress:
        progress("Comparaison avec les versions installées…")
    s = list_updates()
    if not ok:
        s.error = erreur
    if s.new_release:
        s.notes = release_notes(s.new_release)
    save_state(s)
    return s


def repo_url():
    """Adresse du dépôt NounoursOS (fournie par nounoursos-archive-keyring)."""
    try:
        with open("/etc/nounoursos/depot.conf") as f:
            for line in f:
                if line.startswith("URL="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return "https://angelgithub17.github.io/nounoursos-apt"


def release_notes(version):
    """Texte « Quoi de neuf » publié avec la version (nouveautes/<version>.md)."""
    if DEMO:
        return ("**Quoi de neuf dans NounoursOS 1.1 ?**\n\n"
                "- Nouveau fond d'écran *Aurore*\n- Paramètres plus rapides\n"
                "- NounoursLauncher 2.4 préinstallé\n- Correctifs de sécurité")
    import urllib.request
    try:
        with urllib.request.urlopen(f"{repo_url()}/nouveautes/{version}.md", timeout=8) as r:
            return r.read(20000).decode("utf-8", "replace")
    except Exception:
        return ""


def save_state(s):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(s.to_json(), f)


def load_state():
    try:
        with open(STATE_FILE) as f:
            return UpdateSet.from_json(json.load(f))
    except Exception:
        return UpdateSet()


def install_command(offline=False):
    """Commande d'installation (lancée par QProcess pour suivre la progression).

    APT via l'action administrateur NounoursOS (pkexec) : demande le mot de passe
    une fois, puis affiche « dlstatus » (téléchargement) et « pmstatus » (installation).
    """
    if DEMO:
        return ["sh", "-c", "for i in $(seq 0 10 100); do echo \"dlstatus:1:$i:Téléchargement\"; sleep 0.05; done; "
                            "for i in $(seq 0 5 100); do echo \"pmstatus:paquet:$i:Installation de paquet\"; "
                            "sleep 0.1; done"]
    from . import HELPER
    return ["pkexec", HELPER, "maj-preparer" if offline else "maj-maintenant"]


STATUS_FR = {
    "Downloading": "Téléchargement des mises à jour…",
    "Installing": "Installation…",
    "Updating": "Installation…",
    "Running": "Préparation…",
    "Waiting for authentication": "En attente de votre mot de passe…",
    "Waiting in queue": "En attente…",
    "Finished": "Finalisation…",
    "Loading cache": "Préparation…",
    "Resolving dependencies": "Préparation…",
    "Testing changes": "Vérification…",
    "Committing changes": "Installation…",
    "Cleaning up": "Nettoyage…",
}


def _demo():
    data = [
        ("nounoursos-release", "1.1-1", "1.0-1", "nounoursos"),
        ("linux-image-amd64", "6.12.48-1", "6.12.43-1", "trixie-security"),
        ("libssl3t64", "3.5.1-1+deb13u2", "3.5.1-1+deb13u1", "trixie-security"),
        ("firefox-esr", "140.5.0esr-1~deb13u1", "140.4.0esr-1~deb13u1", "trixie-security"),
        ("plasma-workspace", "4:6.3.6-2", "4:6.3.6-1", "trixie-updates"),
        ("nounoursos-launcher", "2.4.0", "2.3.1", "nounoursos"),
        ("tzdata", "2026c-0+deb13u1", "2026b-0+deb13u1", "trixie-updates"),
    ]
    sizes = [12_000, 98_500_000, 2_400_000, 71_000_000, 9_800_000, 31_000_000, 260_000]
    return UpdateSet([Update(n, new, old, s, sz) for (n, new, old, s), sz in zip(data, sizes)],
                     time.time(), notes=release_notes("1.1"))
