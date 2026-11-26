"""Modes Concentration NounoursOS : Travail, Jeu, Stream.

Un mode peut : couper les notifications (« Ne pas déranger »), changer le fond d'écran
(l'ancien revient à la sortie), ouvrir des applications, et s'activer seul à heure fixe.

Réglages et état : ~/.config/nounoursos/concentration.json. Le service
« nounoursos-concentration --service » (lancé à l'ouverture de session) applique l'état :
il garde l'inhibition des notifications auprès de Plasma (org.freedesktop.Notifications
Inhibit/UnInhibit, qui dure tant que le service est connecté) et suit les horaires.
N'importe pas Qt.
"""
import copy
import json
import os
import time

CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "nounoursos")
FICHIER = os.path.join(CONFIG_DIR, "concentration.json")

MODES_DEFAUT = {
    "travail": {"nom": "Travail", "icone": "💼", "ne_pas_deranger": True, "fond": "", "applis": [],
                "horaire": {"actif": False, "debut": "09:00", "fin": "17:00", "jours": [1, 2, 3, 4, 5]}},
    "jeu": {"nom": "Jeu", "icone": "🎮", "ne_pas_deranger": True, "fond": "", "applis": [],
            "horaire": {"actif": False, "debut": "20:00", "fin": "23:00", "jours": [1, 2, 3, 4, 5, 6, 7]}},
    "stream": {"nom": "Stream", "icone": "🔴", "ne_pas_deranger": True, "fond": "", "applis": [],
               "horaire": {"actif": False, "debut": "18:30", "fin": "20:00", "jours": [1, 2, 3, 4]}},
}


def lire():
    d = {"actif": None, "par_horaire": False, "ndp": False, "modes": copy.deepcopy(MODES_DEFAUT)}
    try:
        with open(FICHIER) as f:
            lu = json.load(f)
        d["actif"] = lu.get("actif")
        d["par_horaire"] = bool(lu.get("par_horaire"))
        d["ndp"] = bool(lu.get("ndp"))
        for k, m in (lu.get("modes") or {}).items():
            base = d["modes"].get(k, {})
            base.update({c: v for c, v in m.items() if c != "horaire"})
            base.setdefault("horaire", {}).update(m.get("horaire") or {})
            d["modes"][k] = base
    except (OSError, ValueError):
        pass
    if d["actif"] not in d["modes"]:
        d["actif"] = None
    return d


def ecrire(d):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = FICHIER + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, FICHIER)


def activer(mode, par_horaire=False):
    d = lire()
    if mode is not None and mode not in d["modes"]:
        raise KeyError(mode)
    d["actif"], d["par_horaire"] = mode, bool(mode and par_horaire)
    ecrire(d)
    return d


def ne_pas_deranger(on):
    """« Ne pas déranger » seul, sans mode (Centre de contrôle)."""
    d = lire()
    d["ndp"] = bool(on)
    ecrire(d)
    return d


def silence(d):
    """Les notifications doivent-elles être coupées ?"""
    m = d["modes"].get(d["actif"]) if d["actif"] else None
    return bool(d["ndp"] or (m and m.get("ne_pas_deranger")))


def regler(mode, **valeurs):
    d = lire()
    d["modes"][mode].update(valeurs)
    ecrire(d)
    return d


def dans_horaire(h, maintenant=None):
    """L'horaire {debut, fin, jours (1 = lundi)} couvre-t-il ce moment ? Gère les plages qui passent minuit."""
    if not h or not h.get("actif"):
        return False
    t = time.localtime(maintenant or time.time())
    minute = t.tm_hour * 60 + t.tm_min
    deb = int(h["debut"][:2]) * 60 + int(h["debut"][3:5])
    fin = int(h["fin"][:2]) * 60 + int(h["fin"][3:5])
    jour = t.tm_wday + 1
    if deb <= fin:
        return jour in h.get("jours", []) and deb <= minute < fin
    # Plage de nuit (ex. 22:00 → 01:00) : le jour qui compte est celui du début
    veille = 7 if jour == 1 else jour - 1
    return (jour in h.get("jours", []) and minute >= deb) or (veille in h.get("jours", []) and minute < fin)


def mode_horaire(d, maintenant=None):
    for k, m in d["modes"].items():
        if dans_horaire(m.get("horaire"), maintenant):
            return k
    return None
