"""Modules de réglage KDE (KCM) affichés DANS Paramètres.

S'appuie sur libnounoursos-kcm.so (src/kcm-pont, paquet nounoursos-desktop),
qui expose KCModuleLoader de KDE en C. Sans cette bibliothèque, on retombe
sur l'ouverture du module dans une fenêtre séparée (kcmshell6).
"""
import ctypes
import json
import os

from PyQt6 import sip
from PyQt6.QtWidgets import QWidget

from . import ROOT

_PATHS = [ROOT + "/usr/lib/nounoursos/libnounoursos-kcm.so",
          "/usr/lib/nounoursos/libnounoursos-kcm.so",
          os.environ.get("NOUNOURSOS_KCM_LIB", "")]
_lib = None
_tried = False
_existe_cache = {}


def _load():
    global _lib, _tried
    if _tried:
        return _lib
    _tried = True
    for p in _PATHS:
        if p and os.path.exists(p):
            try:
                lib = ctypes.CDLL(p)
            except OSError as e:
                print("NounoursOS : pont KCM indisponible :", e)
                continue
            lib.nkcm_charger.restype = ctypes.c_void_p
            lib.nkcm_charger.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
            lib.nkcm_widget.restype = ctypes.c_void_p
            lib.nkcm_widget.argtypes = [ctypes.c_void_p]
            for f in ("nkcm_enregistrer", "nkcm_recharger", "nkcm_par_defaut"):
                getattr(lib, f).argtypes = [ctypes.c_void_p]
            lib.nkcm_a_enregistrer.argtypes = [ctypes.c_void_p]
            lib.nkcm_existe.argtypes = [ctypes.c_char_p]
            lib.nkcm_liste.restype = ctypes.c_char_p
            _lib = lib
            break
    return _lib


def disponible():
    return _load() is not None


def existe(kcm_id):
    """Le module est-il installé ? (sans le pont, on suppose que oui)"""
    lib = _load()
    if lib is None:
        return True
    if kcm_id not in _existe_cache:
        _existe_cache[kcm_id] = bool(lib.nkcm_existe(kcm_id.encode()))
    return _existe_cache[kcm_id]


def liste():
    lib = _load()
    if lib is None:
        return []
    try:
        return json.loads(lib.nkcm_liste().decode("utf-8"))
    except Exception:
        return []


class Module:
    """Un module KDE chargé ; .widget est à placer dans la page."""

    def __init__(self, kcm_id):
        self.id = kcm_id
        self.handle = None
        self.widget = None
        lib = _load()
        if lib is None:
            return
        # Parent nu (sans layout) : le module y crée son widget, qu'on replace ensuite
        self._parent = QWidget()
        h = lib.nkcm_charger(kcm_id.encode(), sip.unwrapinstance(self._parent))
        if not h:
            return
        self.handle = h
        self.widget = sip.wrapinstance(lib.nkcm_widget(h), QWidget)

    @property
    def ok(self):
        return self.handle is not None

    def a_enregistrer(self):
        return bool(self.ok and _lib.nkcm_a_enregistrer(self.handle))

    def enregistrer(self):
        if self.ok:
            _lib.nkcm_enregistrer(self.handle)

    def recharger(self):
        if self.ok:
            _lib.nkcm_recharger(self.handle)

    def par_defaut(self):
        if self.ok:
            _lib.nkcm_par_defaut(self.handle)
