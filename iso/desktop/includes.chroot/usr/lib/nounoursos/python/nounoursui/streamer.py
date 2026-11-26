"""Kit streamer : OBS Studio prêt à l'emploi (profil + scènes NounoursOS).

- Profil « NounoursOS » : 1080p 60 i/s, réglages simples, enregistrements dans Vidéos
- Scènes « NounoursOS » : Ça commence bientôt, En direct (écran + caméra + cadre), Pause, Fin
- Plateforme : Twitch, YouTube ou Kick ; la clé de stream reste dans la configuration d'OBS (0600)
Ne remplace jamais une configuration existante sans qu'on le demande. N'importe pas Qt.
"""
import configparser
import json
import os
import shutil
import subprocess
import uuid

OBS = os.path.expanduser("~/.config/obs-studio")
NOM = "NounoursOS"
IMAGES = "/usr/share/nounoursos/streamer"
CAM = (1440, 750, 420, 236)

PLATEFORMES = {
    "twitch": {"nom": "Twitch", "type": "rtmp_common", "service": "Twitch", "serveur": "auto",
               "cle": "https://dashboard.twitch.tv/settings/stream"},
    "youtube": {"nom": "YouTube", "type": "rtmp_common", "service": "YouTube - RTMPS",
                "serveur": "rtmps://a.rtmps.youtube.com:443/live2",
                "cle": "https://studio.youtube.com/"},
    "kick": {"nom": "Kick", "type": "rtmp_custom", "service": None,
             "serveur": "rtmps://fa723fc1b171.global-contribute.live-video.net:443/app/",
             "cle": "https://dashboard.kick.com/"},
    "autre": {"nom": "Autre (Restream, serveur RTMP…)", "type": "rtmp_custom", "service": None, "serveur": "",
              "cle": None},
}


def obs_installe():
    return bool(shutil.which("obs"))


def kit_present():
    return os.path.exists(os.path.join(OBS, "basic", "scenes", NOM + ".json"))


def _uuid():
    return str(uuid.uuid4())


def _source(nom, ident, reglages=None, audio=False):
    return {"name": nom, "uuid": _uuid(), "id": ident, "versioned_id": ident, "settings": reglages or {},
            "mixers": 255 if audio else 0, "sync": 0, "flags": 0, "volume": 1.0, "balance": 0.5,
            "enabled": True, "muted": False, "push-to-mute": False, "push-to-talk": False,
            "hotkeys": {}, "deinterlace_mode": 0, "deinterlace_field_order": 0, "monitoring_type": 0,
            "private_settings": {}, "filters": []}


def _element(src, n, x=0, y=0, w=None, h=None):
    el = {"name": src["name"], "source_uuid": src["uuid"], "visible": True, "locked": False, "rot": 0.0,
          "pos": {"x": float(x), "y": float(y)}, "scale": {"x": 1.0, "y": 1.0}, "align": 5,
          "bounds_type": 0, "bounds_align": 0, "bounds_crop": False, "bounds": {"x": 0.0, "y": 0.0},
          "crop_left": 0, "crop_top": 0, "crop_right": 0, "crop_bottom": 0, "id": n,
          "group_item_backup": False, "scale_filter": "disable", "blend_method": "default",
          "blend_type": "normal", "show_transition": {"duration": 0}, "hide_transition": {"duration": 0},
          "private_settings": {}}
    if w and h:                      # s'adapte à la taille de la source (2 = ajuster en gardant le rapport)
        el["bounds_type"] = 2
        el["bounds"] = {"x": float(w), "y": float(h)}
    return el


def _scene(nom, elements):
    s = _source(nom, "scene", {"id_counter": len(elements), "custom_size": False,
                               "items": [_element(*e[:1], i + 1, *e[1:]) for i, e in enumerate(elements)]})
    s["canvas_uuid"] = ""
    return s


def collection(wayland=True):
    img = lambda n, f: _source(n, "image_source", {"file": f"{IMAGES}/{f}", "unload": False})
    bientot, pause, fin = img("Écran Bientôt", "bientot.png"), img("Écran Pause", "pause.png"), \
        img("Écran Fin", "fin.png")
    cadre = img("Cadre caméra", "cadre-camera.png")
    ecran = (_source("Mon écran", "pipewire-screen-capture-source", {"ShowCursor": True}) if wayland else
             _source("Mon écran", "xshm_input", {"show_cursor": True}))
    camera = _source("Caméra", "v4l2_input", {"device_id": "/dev/video0", "auto_reset": True})
    micro = _source("Micro", "pulse_input_capture", {"device_id": "default"}, audio=True)
    son = _source("Son du bureau", "pulse_output_capture", {"device_id": "default"}, audio=True)
    x, y, w, h = CAM
    scenes = [
        _scene("Ça commence bientôt", [(bientot,)]),
        _scene("En direct", [(ecran, 0, 0, 1920, 1080), (camera, x, y, w, h), (cadre,)]),
        _scene("Pause", [(pause,)]),
        _scene("Fin du live", [(fin,)]),
    ]
    sources = [bientot, pause, fin, cadre, ecran, camera] + scenes
    return {
        "name": NOM, "current_scene": "Ça commence bientôt", "current_program_scene": "Ça commence bientôt",
        "scene_order": [{"name": s["name"]} for s in scenes], "sources": sources, "groups": [],
        "transitions": [], "current_transition": "Fade", "transition_duration": 400,
        "DesktopAudioDevice1": dict(son, name="Son du bureau"), "AuxAudioDevice1": dict(micro, name="Micro"),
        "quick_transitions": [], "saved_projectors": [], "preview_locked": False, "scaling_enabled": False,
        "modules": {}, "version": 2,
    }


def _ini(chemin, sections):
    cp = configparser.RawConfigParser()
    cp.optionxform = str
    if os.path.exists(chemin):
        try:
            cp.read(chemin, encoding="utf-8-sig")
        except configparser.Error:
            pass
    for sec, vals in sections.items():
        if not cp.has_section(sec):
            cp.add_section(sec)
        for k, v in vals.items():
            cp.set(sec, k, str(v))
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        cp.write(f, space_around_delimiters=False)


def dossier_videos():
    try:
        d = subprocess.run(["xdg-user-dir", "VIDEOS"], capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        d = ""
    return d if d and d != os.path.expanduser("~") else os.path.expanduser("~/Vidéos")


def preparer(ecraser=False):
    """Installe le profil et les scènes NounoursOS dans OBS et les sélectionne."""
    scenes = os.path.join(OBS, "basic", "scenes", NOM + ".json")
    if os.path.exists(scenes) and not ecraser:
        return False
    os.makedirs(os.path.dirname(scenes), exist_ok=True)
    wayland = os.environ.get("XDG_SESSION_TYPE", "wayland") != "x11"
    with open(scenes, "w", encoding="utf-8") as f:
        json.dump(collection(wayland), f, indent=4, ensure_ascii=False)
    videos = dossier_videos()
    os.makedirs(videos, exist_ok=True)
    _ini(os.path.join(OBS, "basic", "profiles", NOM, "basic.ini"), {
        "General": {"Name": NOM},
        "Video": {"BaseCX": 1920, "BaseCY": 1080, "OutputCX": 1920, "OutputCY": 1080, "FPSType": 0,
                  "FPSCommon": 60, "ScaleType": "bicubic"},
        "Output": {"Mode": "Simple"},
        "SimpleOutput": {"VBitrate": 6000, "ABitrate": 160, "StreamEncoder": "x264", "Preset": "veryfast",
                         "RecFormat2": "mkv", "RecQuality": "Stream", "FilePath": videos},
        "Audio": {"SampleRate": 48000, "ChannelSetup": "Stereo"},
    })
    _ini(os.path.join(OBS, "global.ini"), {
        "General": {"FirstRun": "true"},
        "Basic": {"Profile": NOM, "ProfileDir": NOM, "SceneCollection": NOM, "SceneCollectionFile": NOM},
    })
    return True


def plateforme():
    """(clé de plateforme, clé de stream renseignée ?)"""
    try:
        with open(os.path.join(OBS, "basic", "profiles", NOM, "service.json"), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None, False
    s = d.get("settings", {})
    for k, p in PLATEFORMES.items():
        if (p["service"] and s.get("service") == p["service"]) or \
                (not p["service"] and p["serveur"] and s.get("server") == p["serveur"]):
            return k, bool(s.get("key"))
    return "autre", bool(s.get("key"))


def serveur_actuel():
    try:
        with open(os.path.join(OBS, "basic", "profiles", NOM, "service.json"), encoding="utf-8") as f:
            return json.load(f).get("settings", {}).get("server", "")
    except (OSError, ValueError):
        return ""


def regler_plateforme(cle_plateforme, cle_stream, serveur=None):
    p = PLATEFORMES[cle_plateforme]
    reglages = {"server": serveur or p["serveur"], "key": cle_stream.strip(), "bwtest": False,
                "use_auth": False}
    if p["service"]:
        reglages["service"] = p["service"]
    chemin = os.path.join(OBS, "basic", "profiles", NOM, "service.json")
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    fd = os.open(chemin + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"type": p["type"], "settings": reglages}, f, indent=4)
    os.replace(chemin + ".tmp", chemin)


def lancer():
    subprocess.Popen(["obs", "--profile", NOM, "--collection", NOM], start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
