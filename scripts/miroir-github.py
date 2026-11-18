#!/usr/bin/env python3
"""Copie le .deb d'une Release GitHub dans dist/, sous un nom à la Debian.

Usage : miroir-github.py <propriétaire/dépôt> <regex du fichier> <paquet attendu> <dossier dist>
Jeton lu dans la variable d'environnement indiquée par TOKEN_VAR (défaut GH_TOKEN) :
indispensable pour un dépôt privé, conseillé pour un public (limite d'appels).
Code retour 0 = copié, 1 = ignoré (non bloquant pour la publication).
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

repo, pattern, expected, dist = sys.argv[1:5]
token = os.environ.get(os.environ.get("TOKEN_VAR", "GH_TOKEN"), "")


def get(url, accept="application/vnd.github+json"):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "nounoursos-apt"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    return urllib.request.urlopen(req, timeout=120)


try:
    rel = json.load(get(f"https://api.github.com/repos/{repo}/releases/latest"))
except Exception as e:
    print(f"⚠  {repo} : release introuvable ({e})", file=sys.stderr)
    sys.exit(1)

asset = next((a for a in rel.get("assets", []) if re.search(pattern, a["name"])), None)
if not asset:
    print(f"⚠  {repo} {rel.get('tag_name')} : aucun fichier ne correspond à {pattern}", file=sys.stderr)
    sys.exit(1)

with tempfile.NamedTemporaryFile(suffix=".deb", delete=False) as tmp:
    with get(asset["url"], "application/octet-stream") as r:
        while chunk := r.read(1 << 20):
            tmp.write(chunk)
    path = tmp.name


def field(name):
    return subprocess.run(["dpkg-deb", "-f", path, name], capture_output=True, text=True).stdout.strip()


if field("Package") != expected:
    print(f"⚠  {asset['name']} : paquet « {field('Package')} » au lieu de « {expected} »", file=sys.stderr)
    os.unlink(path)
    sys.exit(1)

# Nom à la Debian (nom_version_arch.deb) : obligatoire pour live-build
version = re.sub(r"^\d+:", "", field("Version"))
dest = os.path.join(dist, f"{expected}_{version}_{field('Architecture')}.deb")
os.replace(path, dest)
os.chmod(dest, 0o644)
print(f"   {repo} {rel.get('tag_name')} → {os.path.basename(dest)}")
