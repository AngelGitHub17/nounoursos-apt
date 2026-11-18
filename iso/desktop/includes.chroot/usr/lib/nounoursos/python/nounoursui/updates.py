"""Moteur des mises à jour NounoursOS.

- Recherche : PackageKit (`pkcon refresh`) puis `apt list --upgradable`.
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


def refresh():
    """Met à jour la liste des paquets (sans droits root, via PackageKit)."""
    if DEMO:
        time.sleep(1.2)
        return True
    if has("pkcon"):
        out = run(["env", "LC_ALL=C", "pkcon", "refresh", "--plain", "--noninteractive"], timeout=600)
        return "Fatal" not in out
    return False


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


def check():
    """Recherche complète + mémorisation pour les autres applis (badge…)."""
    ok = refresh()
    s = list_updates()
    if not ok and not DEMO:
        s.error = "La liste des mises à jour n'a pas pu être rafraîchie (connexion ?)."
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
