"""NounoursAccount dans NounoursOS : connexion par code, comme NounoursLauncher.

1. auth/start  → un code (ABCD-EFGH) et l'adresse de la page connect.php ;
2. l'utilisateur valide le code sur le site, déjà connecté à NounoursAccount ;
3. auth/poll   → un jeton « nlu_… » propre à cet ordinateur ;
4. auth/me     → profil (nom, pseudo, avatar, pièces).
Le jeton reste dans ~/.config/nounoursos/compte.json (lisible par l'utilisateur seul).
N'importe pas Qt.
"""
import json
import os
import socket
import urllib.error
import urllib.request

API = os.environ.get("NOUNOURSOS_ACCOUNT_API", "https://nounourscorp.fr/launcher/api.php")
CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "nounoursos")
CACHE_DIR = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "nounoursos")
FICHIER = os.path.join(CONFIG_DIR, "compte.json")
AVATAR = os.path.join(CACHE_DIR, "avatar")

SITES = [
    ("NounoursCorp", "https://nounourscorp.fr/"),
    ("NSDKPlus", "https://nsdkplus.fr/"),
    ("NounoursTV", "https://ntvbydidikaria.fr/"),
    ("NounoursScreenInfo", "https://nounoursscreeninfo.fr/"),
    ("DidiKaria", "https://didikaria.fr/"),
]


class ErreurCompte(Exception):
    pass


def _appel(route, donnees=None, jeton=None, delai=15):
    url = f"{API}?r={route}"
    corps = json.dumps(donnees).encode() if donnees is not None else None
    req = urllib.request.Request(url, data=corps, method="POST" if corps is not None else "GET",
                                 headers={"User-Agent": "NounoursOS", "Accept": "application/json"})
    if corps is not None:
        req.add_header("Content-Type", "application/json")
    if jeton:
        req.add_header("Authorization", f"Bearer {jeton}")
    try:
        with urllib.request.urlopen(req, timeout=delai) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get("error") or e.reason
        except Exception:
            msg = e.reason
        if e.code == 401:
            raise ErreurCompte("La connexion a expiré : reconnectez-vous.") from e
        raise ErreurCompte(str(msg)) from e
    except (urllib.error.URLError, socket.timeout, OSError) as e:
        raise ErreurCompte("NounoursAccount est injoignable. Vérifiez votre connexion à Internet.") from e
    except ValueError as e:
        raise ErreurCompte("Réponse inattendue de NounoursAccount.") from e


# --- Connexion ---------------------------------------------------------------------
def commencer():
    """Renvoie {code, url, poll, expires_in}."""
    return _appel("auth/start", {"label": f"NounoursOS ({socket.gethostname()})"})


def verifier(poll):
    """None tant que le code n'est pas validé, sinon le profil (et le jeton est enregistré)."""
    r = _appel("auth/poll", {"poll": poll})
    if r.get("pending"):
        return None
    jeton, user = r.get("token"), r.get("user") or {}
    if not jeton:
        raise ErreurCompte("Réponse inattendue de NounoursAccount.")
    _enregistrer(jeton, user)
    return user


def _enregistrer(jeton, user):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    ancien = os.umask(0o077)
    try:
        with open(FICHIER, "w") as f:
            json.dump({"token": jeton, "user": user}, f)
    finally:
        os.umask(ancien)
    os.chmod(FICHIER, 0o600)
    telecharger_avatar(user)


def lire():
    try:
        with open(FICHIER) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def utilisateur():
    """Profil mémorisé (sans réseau), ou None si pas connecté."""
    return lire().get("user") or None


def actualiser():
    """Recharge le profil depuis NounoursAccount (nom, pièces…). Déconnecte si le jeton est refusé."""
    d = lire()
    if not d.get("token"):
        return None
    try:
        r = _appel("auth/me", jeton=d["token"])
    except ErreurCompte as e:
        if "expiré" in str(e):
            deconnecter(local_seulement=True)
            return None
        raise
    user = r.get("user")
    if not user:
        deconnecter(local_seulement=True)
        return None
    _enregistrer(d["token"], user)
    return user


def deconnecter(local_seulement=False):
    d = lire()
    if d.get("token") and not local_seulement:
        try:
            _appel("auth/logout", {}, jeton=d["token"], delai=8)
        except ErreurCompte:
            pass
    for f in (FICHIER, AVATAR):
        try:
            os.unlink(f)
        except OSError:
            pass


def telecharger_avatar(user):
    url = (user or {}).get("avatar")
    if not url or not str(url).startswith(("https://", "http://")):
        return None
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "NounoursOS"})
        with urllib.request.urlopen(req, timeout=10) as r, open(AVATAR, "wb") as f:
            f.write(r.read(4 * 1024 * 1024))
        return AVATAR
    except (urllib.error.URLError, OSError):
        return None
