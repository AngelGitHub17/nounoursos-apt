#!/usr/bin/env bash
# =============================================================================
#  Construit les paquets .deb de NounoursOS dans dist/
#  Usage : ./scripts/construire-paquets.sh
#
#  - nounoursos-release           : identité et version du système (os-release)
#  - nounoursos-desktop           : applis NounoursOS, thème, fonds d'écran, icônes
#  - nounoursos-archive-keyring   : clé de signature + source APT du dépôt
#
#  Les fichiers viennent directement de iso/ : une seule source pour l'ISO
#  et pour les mises à jour des machines déjà installées.
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Numéro de build = nombre de commits : ne change que si le projet change
RUN="$(git -C "$ROOT" rev-list --count HEAD 2>/dev/null || echo 0)"
ISO="$ROOT/iso"
# shellcheck source=/dev/null
. "$ISO/VERSION"          # VERSION, CODENAME, DEBIAN_BASE
# shellcheck source=/dev/null
. "$ROOT/depot.conf"      # URL, SUITE, COMPONENT

OUT="$ROOT/dist"
WORK="$ROOT/.build"
rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$WORK"

MAINTAINER="NounoursCorp <depot@nounourscorp.fr>"
DESKTOP_VERSION="${VERSION}+git${RUN}"   # change à chaque commit
RELEASE_VERSION="${VERSION}"             # ne change que quand iso/VERSION change
KEYRING_VERSION="1"

log() { printf '\033[1;33m🐻 %s\033[0m\n' "$*"; }

# Copie un chemin de iso/ vers le paquet en gardant l'arborescence
take() {  # take <pkgdir> <base> <chemin relatif (glob autorisé)>
  local pkg="$1" base="$2" pattern="$3" p
  shopt -s nullglob
  for p in "$base"/$pattern; do
    local rel="${p#"$base"/}"
    mkdir -p "$pkg/$(dirname "$rel")"
    cp -a "$p" "$pkg/$rel"
  done
  shopt -u nullglob
}

build() {  # build <pkgdir>
  local pkg="$1"
  find "$pkg" -name __pycache__ -prune -exec rm -rf {} +
  # md5sums (vérification d'intégrité par dpkg)
  ( cd "$pkg" && find . -type f ! -path './DEBIAN/*' -printf '%P\0' | sort -z | xargs -0r md5sum > DEBIAN/md5sums )
  # conffiles : tout ce qui est dans /etc
  if [ -d "$pkg/etc" ]; then
    ( cd "$pkg" && find etc -type f -printf '/%p\n' | sort > DEBIAN/conffiles )
  fi
  local size
  size=$(du -sk --exclude=DEBIAN "$pkg" | cut -f1)
  sed -i "s/@SIZE@/$size/" "$pkg/DEBIAN/control"
  chmod 755 "$pkg/DEBIAN"
  find "$pkg/DEBIAN" -maxdepth 1 -type f \( -name postinst -o -name prerm -o -name postrm -o -name preinst \) -exec chmod 755 {} +
  dpkg-deb --root-owner-group -Zxz --build "$pkg" "$OUT/" >/dev/null
}

# -----------------------------------------------------------------------------
log "nounoursos-release $RELEASE_VERSION"
P="$WORK/nounoursos-release"
mkdir -p "$P/DEBIAN" "$P/usr/share/nounoursos"
cat > "$P/usr/share/nounoursos/os-release.in" <<EOF
PRETTY_NAME="@PRETTY@ ${VERSION} (${CODENAME})"
NAME="NounoursOS"
VERSION_ID="${VERSION}"
VERSION="${VERSION} (${CODENAME})"
VERSION_CODENAME=${DEBIAN_BASE}
DEBIAN_CODENAME=${DEBIAN_BASE}
NOUNOURSOS_CODENAME="${CODENAME}"
NOUNOURSOS_EDITION=@EDITION@
ID=nounoursos
ID_LIKE=debian
HOME_URL="https://nounourscorp.fr/"
SUPPORT_URL="https://nounourscorp.fr/"
BUG_REPORT_URL="https://nounourscorp.fr/"
LOGO=nounoursos
EOF
printf '@PRETTY@ %s (%s) \\n \\l\n\n' "$VERSION" "$CODENAME" > "$P/usr/share/nounoursos/issue.in"
printf '@PRETTY@ %s (%s)\n' "$VERSION" "$CODENAME" > "$P/usr/share/nounoursos/issue.net.in"
cat > "$P/DEBIAN/control" <<EOF
Package: nounoursos-release
Version: ${RELEASE_VERSION}
Architecture: all
Maintainer: ${MAINTAINER}
Installed-Size: @SIZE@
Section: misc
Priority: important
Homepage: https://nounourscorp.fr/
Description: Version de NounoursOS (${VERSION} « ${CODENAME} »)
 Identité du système NounoursOS : /etc/os-release, /etc/issue.
 Une nouvelle version de ce paquet = une nouvelle version de NounoursOS.
EOF
cat > "$P/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
  ed=desktop
  grep -q '^NOUNOURSOS_EDITION=server' /usr/lib/os-release 2>/dev/null && ed=server
  if [ "$ed" = server ]; then pretty="NounoursOS Server"; else pretty="NounoursOS"; fi
  for f in /usr/lib/os-release /etc/issue /etc/issue.net; do
    if ! dpkg-divert --list "$f" | grep -q "$f.debian"; then
      dpkg-divert --local --rename --divert "$f.debian" --add "$f"
    fi
  done
  sed -e "s/@EDITION@/$ed/" -e "s/@PRETTY@/$pretty/" /usr/share/nounoursos/os-release.in > /usr/lib/os-release
  ln -sf ../usr/lib/os-release /etc/os-release
  sed -e "s/@PRETTY@/$pretty/" /usr/share/nounoursos/issue.in > /etc/issue
  sed -e "s/@PRETTY@/$pretty/" /usr/share/nounoursos/issue.net.in > /etc/issue.net
fi
exit 0
EOF
build "$P"

# -----------------------------------------------------------------------------
log "nounoursos-desktop $DESKTOP_VERSION"
P="$WORK/nounoursos-desktop"
D="$ISO/desktop/includes.chroot"
C="$ISO/common/includes.chroot"
mkdir -p "$P/DEBIAN"
take "$P" "$D" "usr/bin/nounoursos-*"
take "$P" "$D" "usr/lib/nounoursos"
take "$P" "$D" "usr/libexec/nounoursos"
take "$P" "$D" "usr/share/applications/nounoursos-*.desktop"
take "$P" "$D" "usr/share/polkit-1/actions/fr.nounourscorp.nounoursos.policy"
take "$P" "$D" "usr/share/plasma/look-and-feel/org.nounoursos.*"
take "$P" "$D" "usr/share/wallpapers/NounoursOS"
take "$P" "$D" "usr/share/nounoursos/plymouth"
take "$P" "$D" "etc/xdg/autostart/nounoursos-*.desktop"
take "$P" "$C" "usr/share/icons/hicolor/*/apps/nounoursos.*"
take "$P" "$C" "usr/share/nounoursos/logo*"
take "$P" "$C" "usr/share/nounoursos/grub-background.png"
chmod 755 "$P"/usr/bin/* "$P"/usr/libexec/nounoursos/*
cat > "$P/DEBIAN/control" <<EOF
Package: nounoursos-desktop
Version: ${DESKTOP_VERSION}
Architecture: all
Maintainer: ${MAINTAINER}
Installed-Size: @SIZE@
Section: x11
Priority: optional
Depends: nounoursos-release, python3, python3-pyqt6, packagekit, packagekit-tools, kdialog, plasma-workspace
Recommends: unattended-upgrades, pciutils, xdg-user-dirs, kde-cli-tools,
 winboat, docker.io, docker-compose, freerdp3-x11
Homepage: https://nounourscorp.fr/
Description: Bureau NounoursOS : applications, thème et fonds d'écran
 Paramètres, assistant de bienvenue, Mise à jour de NounoursOS,
 dispositions Classique et Mac, fond d'écran et icônes NounoursOS.
EOF
cat > "$P/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
  gtk-update-icon-cache -f -q /usr/share/icons/hicolor 2>/dev/null || true
  python3 -m compileall -q /usr/lib/nounoursos/python 2>/dev/null || true
fi
exit 0
EOF
cat > "$P/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e
find /usr/lib/nounoursos/python -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
exit 0
EOF
build "$P"

# -----------------------------------------------------------------------------
log "nounoursos-archive-keyring $KEYRING_VERSION"
P="$WORK/nounoursos-archive-keyring"
mkdir -p "$P/DEBIAN" "$P/usr/share/keyrings" "$P/etc/apt/sources.list.d" "$P/etc/nounoursos"
if gpg --list-secret-keys >/dev/null 2>&1 && [ -n "$(gpg --list-secret-keys --with-colons 2>/dev/null)" ]; then
  gpg --export > "$P/usr/share/keyrings/nounoursos-archive-keyring.gpg"
elif [ -f "$ROOT/nounoursos.asc" ]; then
  gpg --dearmor < "$ROOT/nounoursos.asc" > "$P/usr/share/keyrings/nounoursos-archive-keyring.gpg"
else
  echo "❌ Aucune clé GPG disponible (voir README : scripts/creer-cle.sh)" >&2; exit 1
fi
cat > "$P/etc/apt/sources.list.d/nounoursos.sources" <<EOF
# Dépôt NounoursOS (mises à jour du système NounoursOS)
Types: deb
URIs: ${URL}
Suites: ${SUITE}
Components: ${COMPONENT}
Signed-By: /usr/share/keyrings/nounoursos-archive-keyring.gpg
EOF
cat > "$P/etc/nounoursos/depot.conf" <<EOF
URL=${URL}
SUITE=${SUITE}
EOF
cat > "$P/DEBIAN/control" <<EOF
Package: nounoursos-archive-keyring
Version: ${KEYRING_VERSION}
Architecture: all
Maintainer: ${MAINTAINER}
Installed-Size: @SIZE@
Section: misc
Priority: important
Homepage: https://nounourscorp.fr/
Description: Clé et source APT du dépôt NounoursOS
 Permet à APT de recevoir et vérifier les mises à jour de NounoursOS.
EOF
build "$P"

# -----------------------------------------------------------------------------
# WinBoat (applications Windows) : copie du dernier .deb officiel dans le dépôt
# NounoursOS -> préinstallé dans l'ISO et mis à jour via « Mise à jour de NounoursOS ».
log "winboat (dernière version officielle)"
AUTH=()
if [ -n "${GH_TOKEN:-}" ]; then AUTH=(-H "Authorization: Bearer $GH_TOKEN"); fi
WB_URL=""
for repo in winboat-org/winboat TibixDev/winboat; do
  WB_URL=$(curl -fsSL "${AUTH[@]}" "https://api.github.com/repos/$repo/releases/latest" 2>/dev/null \
           | grep -oE '"browser_download_url": *"[^"]*amd64\.deb"' | head -1 | sed -E 's/.*"(https[^"]+)"/\1/') || true
  [ -n "$WB_URL" ] && break
done
WB_TMP="$WORK/winboat.deb"
if [ -n "$WB_URL" ] && curl -fsSL -o "$WB_TMP" "$WB_URL" \
   && dpkg-deb -f "$WB_TMP" Package | grep -qx winboat; then
  # Nom à la Debian (nom_version_arch.deb) : obligatoire pour live-build
  WB_NAME="winboat_$(dpkg-deb -f "$WB_TMP" Version | sed 's/^[0-9]*://')_$(dpkg-deb -f "$WB_TMP" Architecture).deb"
  mv "$WB_TMP" "$OUT/$WB_NAME"
  echo "   $WB_NAME"
else
  rm -f "$OUT"/winboat*.deb
  echo "⚠  WinBoat non récupéré : le dépôt est publié sans lui (non bloquant)." >&2
fi

log "Paquets prêts :"
ls -1 "$OUT"
