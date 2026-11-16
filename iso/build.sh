#!/usr/bin/env bash
# =============================================================================
#  NounoursOS — script de construction des ISO
#  Usage : sudo ./build.sh [desktop|server]
#          sudo CLEAN=1 ./build.sh desktop    (repart de zéro, vide aussi le cache)
#  À lancer sur une machine/VM Debian 13 (Trixie).
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
EDITION="${1:-desktop}"
# shellcheck source=VERSION
. "$ROOT/VERSION"

case "$EDITION" in
  desktop) PRETTY="NounoursOS" ;;
  server)  PRETTY="NounoursOS Server" ;;
  *) echo "Usage : sudo $0 [desktop|server]" >&2; exit 1 ;;
esac

log() { printf '\n\033[1;33m🐻 %s\033[0m\n' "$*"; }

# --- Vérifications ------------------------------------------------------------
[ "$(id -u)" -eq 0 ] || { echo "Ce script doit être lancé avec sudo." >&2; exit 1; }

if ! grep -q 'VERSION_CODENAME=trixie' /etc/os-release 2>/dev/null; then
  echo "⚠  L'hôte n'est pas une Debian 13 (Trixie). Le build peut échouer." >&2
  read -r -p "Continuer quand même ? [o/N] " r; [ "$r" = "o" ] || exit 1
fi

# "su" sans tiret ne met pas /usr/sbin dans le PATH (chroot, debootstrap…)
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Debian installée depuis un DVD : APT pointe encore vers le cédérom
if grep -rqs '^[[:space:]]*deb[[:space:]]\+cdrom:' /etc/apt/sources.list /etc/apt/sources.list.d/; then
  echo "❌ APT utilise encore le DVD d'installation (lignes 'deb cdrom:')." >&2
  echo "   Corrige les sources APT (voir README, section 1), puis relance." >&2
  exit 1
fi

if ! command -v lb >/dev/null; then
  log "Installation de live-build"
  apt-get update
  apt-get install -y live-build
fi
command -v lb >/dev/null || { echo "❌ live-build n'a pas pu être installé." >&2; exit 1; }

FREE_GB=$(df -BG --output=avail "$ROOT" | tail -1 | tr -dc '0-9')
[ "$FREE_GB" -ge 20 ] || echo "⚠  Seulement ${FREE_GB} Go libres, 20 Go recommandés." >&2

# --- Préparation du dossier de build --------------------------------------------
BUILD="$ROOT/build/$EDITION"
mkdir -p "$BUILD" "$ROOT/out"
cd "$BUILD"

if [ "${CLEAN:-0}" = "1" ]; then
  log "Nettoyage complet (cache compris)"
  lb clean --purge || true
else
  lb clean || true          # garde le cache des paquets => builds suivants bien plus rapides
fi
rm -rf config

# --- Configuration live-build ------------------------------------------------------
log "Configuration de $PRETTY $VERSION ($EDITION)"

COMMON_OPTS=(
  --mode debian
  --distribution "$DEBIAN_BASE"
  --architectures amd64
  --archive-areas "main contrib non-free non-free-firmware"
  --mirror-bootstrap "http://deb.debian.org/debian/"
  --mirror-binary    "http://deb.debian.org/debian/"
  --security true
  --updates true
  --firmware-chroot true
  --firmware-binary true
  --apt-recommends true
  --binary-images iso-hybrid
  --memtest none
  --iso-application "$PRETTY"
  --iso-publisher   "NounoursCorp - https://nounourscorp.fr"
  --iso-volume      "NounoursOS ${VERSION}"
  --image-name      "NounoursOS-${EDITION}-${VERSION}"
)

if [ "$EDITION" = "desktop" ]; then
  lb config "${COMMON_OPTS[@]}" \
    --debian-installer none \
    --bootappend-live "boot=live components quiet splash locales=fr_FR.UTF-8 keyboard-layouts=fr username=nounours user-fullname=Nounours hostname=nounoursos"
else
  lb config "${COMMON_OPTS[@]}" \
    --debian-installer live \
    --debian-installer-gui false \
    --bootappend-live "boot=live components locales=fr_FR.UTF-8 keyboard-layouts=fr username=nounours user-fullname=Nounours hostname=nounoursos-server"
fi

# --- Copie de nos fichiers : commun puis édition --------------------------------------
log "Copie des fichiers NounoursOS"
cp -a "$ROOT/common/." config/
cp -a "$ROOT/$EDITION/." config/
chmod +x config/hooks/live/*.hook.chroot 2>/dev/null || true
find config/includes.chroot/usr/bin config/includes.chroot/usr/local/bin -type f -exec chmod +x {} + 2>/dev/null || true

# Dépôt NounoursOS (GitHub Pages) : s'il est en ligne, l'ISO l'utilise et
# installe les paquets NounoursOS -> les machines recevront les mises à jour.
if [ -f "$ROOT/../depot.conf" ]; then
  # shellcheck source=/dev/null
  . "$ROOT/../depot.conf"
  mkdir -p config/archives
  if curl -fsSL --max-time 20 "$URL/nounoursos.asc" -o config/archives/nounoursos.key.chroot \
     && curl -fsSL --max-time 20 -o /dev/null "$URL/dists/$SUITE/InRelease"; then
    log "Dépôt NounoursOS trouvé : $URL"
    echo "deb $URL $SUITE $COMPONENT" > config/archives/nounoursos.list.chroot
    {
      echo "nounoursos-archive-keyring"
      echo "nounoursos-release"
      if [ "$EDITION" = "desktop" ]; then echo "nounoursos-desktop"; fi
    } > config/package-lists/nounoursos-depot.list.chroot
  else
    rm -f config/archives/nounoursos.key.chroot
    echo "⚠  Dépôt NounoursOS injoignable ($URL) : ISO construite sans lui (pas de mises à jour NounoursOS)." >&2
  fi
fi

# Fichiers de version générés (une seule source de vérité : VERSION)
mkdir -p config/includes.chroot/usr/share/nounoursos
cat > config/includes.chroot/usr/share/nounoursos/os-release <<EOF
PRETTY_NAME="${PRETTY} ${VERSION} (${CODENAME})"
NAME="NounoursOS"
VERSION_ID="${VERSION}"
VERSION="${VERSION} (${CODENAME})"
VERSION_CODENAME=${DEBIAN_BASE}
DEBIAN_CODENAME=${DEBIAN_BASE}
NOUNOURSOS_CODENAME="${CODENAME}"
NOUNOURSOS_EDITION=${EDITION}
ID=nounoursos
ID_LIKE=debian
HOME_URL="https://nounourscorp.fr/"
SUPPORT_URL="https://nounourscorp.fr/"
BUG_REPORT_URL="https://nounourscorp.fr/"
LOGO=nounoursos
EOF
printf '%s %s (%s) \\n \\l\n\n' "$PRETTY" "$VERSION" "$CODENAME" > config/includes.chroot/usr/share/nounoursos/issue
printf '%s %s (%s)\n' "$PRETTY" "$VERSION" "$CODENAME" > config/includes.chroot/usr/share/nounoursos/issue.net

# --- Build --------------------------------------------------------------------------
log "Construction de l'ISO (30 à 60 min la première fois)"
START=$(date +%s)
lb build 2>&1 | tee "$BUILD/build.log"

ISO=$(ls -t "$BUILD"/*.iso 2>/dev/null | head -1 || true)
[ -n "$ISO" ] || { echo "❌ Pas d'ISO produite, regarde $BUILD/build.log" >&2; exit 1; }

DEST="$ROOT/out/NounoursOS-${EDITION}-${VERSION}-amd64.iso"
mv "$ISO" "$DEST"
( cd "$ROOT/out" && sha256sum "$(basename "$DEST")" > "$(basename "$DEST").sha256" )

log "Terminé en $(( ($(date +%s) - START) / 60 )) min : $DEST ($(du -h "$DEST" | cut -f1))"
