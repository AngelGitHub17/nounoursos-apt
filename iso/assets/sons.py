#!/usr/bin/env python3
"""Sons NounoursOS : notes douces façon marimba en bois, en fa majeur pentatonique.

Chaque son est une courte suite de notes (synthèse : fondamentale + partiels du
marimba, attaque feutrée, petite réverbération). Sortie : thème sonore freedesktop
/usr/share/sounds/nounoursos (Ogg Vorbis).
Usage : python3 iso/assets/sons.py   (numpy et ffmpeg requis)
"""
import os
import subprocess
import tempfile
import wave

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "desktop", "includes.chroot", "usr", "share", "sounds", "nounoursos", "stereo")
TAUX = 48000

NOTES = {n: 440 * 2 ** ((i - 9) / 12 + o - 4)
         for o in range(2, 8) for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A",
                                                       "A#", "B"]) for n in [f"{n}{o}"]}


def note(freq, duree=1.2, force=1.0, brillance=1.0):
    t = np.arange(int(TAUX * duree)) / TAUX
    # Partiels du marimba : fondamentale, ~4x et ~9.9x, qui s'éteignent de plus en plus vite
    son = (np.sin(2 * np.pi * freq * t) * np.exp(-t * 3.2)
           + 0.28 * brillance * np.sin(2 * np.pi * freq * 3.98 * t) * np.exp(-t * 11)
           + 0.08 * brillance * np.sin(2 * np.pi * freq * 9.9 * t) * np.exp(-t * 26))
    # Légère vibration de bois (deuxième mode très amorti)
    son += 0.12 * np.sin(2 * np.pi * freq * 2.01 * t) * np.exp(-t * 7)
    attaque = np.clip(t / 0.004, 0, 1)            # maillet feutré : pas de clic
    return son * attaque * force


def sequence(notes, duree_totale=None, reverb=0.22):
    """notes : [(instant s, nom de note, force)]"""
    fin = max(t for t, _, _ in notes) + 1.3
    duree = duree_totale or fin
    mono = np.zeros(int(TAUX * duree) + TAUX)
    for t, n, f in notes:
        s = note(NOTES[n], force=f, brillance=0.8 if NOTES[n] > 1000 else 1.0)
        i = int(t * TAUX)
        mono[i:i + len(s)] += s[: len(mono) - i]
    # Réverbération simple : quelques échos amortis et décorrélés gauche/droite
    gauche, droite = mono.copy(), mono.copy()
    for retard, gain in ((0.031, 0.5), (0.047, 0.42), (0.071, 0.33), (0.113, 0.22), (0.157, 0.14)):
        d = int(retard * TAUX)
        gauche[d:] += reverb * gain * mono[:-d]
        droite[int(d * 1.13):] += reverb * gain * mono[:-int(d * 1.13)]
    st = np.stack([gauche, droite], axis=1)[: int(TAUX * duree)]
    # Fondu de fin et normalisation douce (sons discrets : -6 dBFS au plus)
    fondu = int(0.25 * TAUX)
    st[-fondu:] *= np.linspace(1, 0, fondu)[:, None]
    st *= 0.5 / max(np.abs(st).max(), 1e-6)
    return st


SONS = {
    "desktop-login": [(0.00, "F4", .8), (0.12, "A4", .8), (0.24, "C5", .85), (0.36, "F5", .9), (0.52, "A5", .7)],
    "desktop-logout": [(0.00, "A5", .7), (0.14, "F5", .75), (0.28, "C5", .8), (0.42, "F4", .85)],
    "message": [(0.00, "C6", .8), (0.11, "F6", .7)],
    "message-new-instant": [(0.00, "A5", .8), (0.09, "D6", .7)],
    "dialog-information": [(0.00, "F5", .7), (0.10, "C6", .6)],
    "dialog-warning": [(0.00, "D5", .8), (0.16, "D5", .65)],
    "dialog-error": [(0.00, "A3", .95), (0.13, "F3", .9)],
    "complete": [(0.00, "F5", .7), (0.08, "A5", .7), (0.16, "C6", .75)],
    "bell": [(0.00, "G5", .7)],
    "bell-window-system": [(0.00, "G5", .7)],
    "device-added": [(0.00, "C5", .75), (0.10, "G5", .75)],
    "device-removed": [(0.00, "G5", .7), (0.10, "C5", .75)],
    "power-plug": [(0.00, "F4", .7), (0.12, "C5", .7)],
    "power-unplug": [(0.00, "C5", .7), (0.12, "F4", .7)],
    "audio-volume-change": [(0.00, "C6", .55)],
    "camera-shutter": [(0.00, "D6", .5), (0.05, "A5", .45)],
    "outcome-success": [(0.00, "C5", .7), (0.10, "F5", .75), (0.20, "A5", .8)],
}
DUREES = {"audio-volume-change": 0.35, "bell": 0.7, "bell-window-system": 0.7, "camera-shutter": 0.5}


def generer():
    os.makedirs(SORTIE, exist_ok=True)
    for nom, notes in SONS.items():
        st = sequence(notes, DUREES.get(nom))
        pcm = (np.clip(st, -1, 1) * 32767).astype("<i2")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = f.name
        with wave.open(tmp, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(TAUX)
            w.writeframes(pcm.tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libvorbis", "-q:a", "4",
                        "-f", "ogg", os.path.join(SORTIE, f"{nom}.oga")], check=True)
        os.unlink(tmp)
    with open(os.path.join(os.path.dirname(SORTIE), "index.theme"), "w") as f:
        f.write("[Sound Theme]\nName=NounoursOS\nName[fr]=NounoursOS\n"
                "Comment=Notes de bois douces, en fa majeur\nInherits=ocean,freedesktop\nDirectories=stereo\n\n"
                "[stereo]\nOutputProfile=stereo\n")
    print(len(SONS), "sons →", SORTIE)


if __name__ == "__main__":
    generer()
