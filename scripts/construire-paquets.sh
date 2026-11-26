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
  # On garde l'édition déjà installée (desktop, server, nt…)
  ed=$(sed -n 's/^NOUNOURSOS_EDITION=//p' /usr/lib/os-release 2>/dev/null | tr -d '"' | head -1)
  case "$ed" in
    server) pretty="NounoursOS Server" ;;
    nt)     pretty="NounoursOS NT" ;;
    *)      ed=desktop; pretty="NounoursOS" ;;
  esac
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
log "nounoursos-nt $DESKTOP_VERSION"
P="$WORK/nounoursos-nt"
N="$ISO/nt/includes.chroot"
mkdir -p "$P/DEBIAN"
take "$P" "$N" "usr/bin/nounoursos-exe"
take "$P" "$N" "usr/bin/nounoursos-libernt"
take "$P" "$N" "usr/share/applications/nounoursos-exe.desktop"
take "$P" "$N" "usr/share/applications/nounoursos-libernt.desktop"
take "$P" "$N" "etc/modules-load.d/nounoursos-ntsync.conf"
take "$P" "$N" "etc/apt/preferences.d/nounoursos-noyau-nt.pref"
take "$P" "$N" "usr/lib/udev/rules.d/70-nounoursos-ntsync.rules"
chmod 755 "$P/usr/bin/nounoursos-exe" "$P/usr/bin/nounoursos-libernt"
cat > "$P/DEBIAN/control" <<EOF
Package: nounoursos-nt
Version: ${DESKTOP_VERSION}
Architecture: all
Maintainer: ${MAINTAINER}
Installed-Size: @SIZE@
Section: otherosfs
Priority: optional
Depends: nounoursos-desktop
Recommends: winehq-stable | wine, winetricks, cabextract, qemu-system-x86, qemu-system-gui, qemu-utils, ovmf
Homepage: https://nounourscorp.fr/
Description: NounoursOS NT : couche de compatibilité Windows
 Ouvre les programmes Windows (.exe, .msi) d'un double-clic avec Wine,
 active le pilote ntsync (synchronisation façon noyau Windows NT) et
 garde le noyau Linux récent de trixie-backports. Permet aussi de démarrer
 LiberNT (système NT libre, projet indépendant) dans une fenêtre.
EOF
cat > "$P/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
  modprobe ntsync 2>/dev/null || true
  udevadm trigger --subsystem-match=misc 2>/dev/null || true
  update-desktop-database -q /usr/share/applications 2>/dev/null || true
fi
exit 0
EOF
chmod 755 "$P/DEBIAN/postinst"
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
take "$P" "$D" "usr/share/wallpapers/NounoursOS*"
take "$P" "$D" "usr/share/color-schemes/NounoursOS*.colors"
take "$P" "$D" "usr/share/plasma/plasmoids/org.nounoursos.*"
take "$P" "$D" "usr/share/plasma/wallpapers/org.nounoursos.*"
take "$P" "$D" "etc/nounoursos"
take "$P" "$D" "usr/share/sddm/themes/nounoursos"
take "$P" "$D" "etc/sddm.conf.d/10-nounoursos.conf"
take "$P" "$C" "usr/share/nounoursos/banniere.png"
take "$P" "$C" "usr/share/icons/hicolor/symbolic/apps/nounoursos-symbolic.svg"
take "$P" "$D" "usr/share/nounoursos/plymouth"
take "$P" "$D" "etc/xdg/autostart/nounoursos-*.desktop"
take "$P" "$D" "usr/share/sounds/nounoursos"
take "$P" "$D" "usr/share/grub/themes/nounoursos"
take "$P" "$D" "usr/share/nounoursos/icones"
take "$P" "$D" "usr/lib/systemd/system/nounoursos-*.service"
take "$P" "$D" "usr/lib/systemd/user/nounoursos-*"
take "$P" "$D" "usr/share/krunner/dbusplugins/nounoursos-*"
take "$P" "$D" "usr/share/dbus-1/services/fr.nounourscorp.*"
take "$P" "$D" "etc/xdg/krunnerrc"
take "$P" "$D" "usr/share/kio/servicemenus/nounoursos-*"
take "$P" "$D" "usr/share/icons/NounoursOS"
take "$P" "$D" "usr/share/nounoursos/streamer"
take "$P" "$D" "etc/xdg/kcminputrc"
take "$P" "$C" "usr/share/icons/hicolor/*/apps/nounoursos.*"
take "$P" "$C" "usr/share/nounoursos/logo*"
take "$P" "$C" "usr/share/nounoursos/grub-background.png"
chmod 755 "$P"/usr/bin/* "$P"/usr/libexec/nounoursos/*
# Pont Paramètres <-> modules KDE (compilé par la CI dans Debian 13) : réglages intégrés
DESK_ARCH=all
DESK_DEPS_EXTRA=""
if [ -f "$ROOT/dist-pont/libnounoursos-kcm.so" ]; then
  install -D -m644 "$ROOT/dist-pont/libnounoursos-kcm.so" "$P/usr/lib/nounoursos/libnounoursos-kcm.so"
  DESK_ARCH=amd64
  DESK_DEPS_EXTRA=", libkf6kcmutils6, libkf6coreaddons6, libqt6widgets6"
else
  echo "   (pont KCM absent : les réglages KDE s'ouvriront dans une fenêtre à part)"
fi
cat > "$P/DEBIAN/control" <<EOF
Package: nounoursos-desktop
Version: ${DESKTOP_VERSION}
Architecture: ${DESK_ARCH}
Maintainer: ${MAINTAINER}
Installed-Size: @SIZE@
Section: x11
Priority: optional
Depends: nounoursos-release, nounoursos-minecraft, python3, python3-pyqt6, packagekit, packagekit-tools, kdialog, plasma-workspace, rsync, python3-dbus, python3-gi${DESK_DEPS_EXTRA}
Recommends: unattended-upgrades, pciutils, xdg-user-dirs, kde-cli-tools,
 winboat, docker.io, docker-compose, freerdp3-x11, nounours-launcher, nounours-browser,
 flatpak, plasma-discover-backend-flatpak, swayidle, fprintd, libpam-fprintd, fonts-inter,
 ksystemstats, qml6-module-org-kde-ksysguard, snapper, btrfs-progs,
 python3-pyqt6.qtpdf, python3-pyqt6.qtmultimedia, poppler-utils, localsend
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
  # « Redémarrer et mettre à jour » : service d'installation au démarrage
  if [ -d /run/systemd/system ]; then systemctl daemon-reload || true; fi
  systemctl enable nounoursos-maj-demarrage.service >/dev/null 2>&1 || true
  # Retour en arrière : prépare snapper si le système est en Btrfs (sans effet sinon)
  systemctl enable nounoursos-instantanes.service >/dev/null 2>&1 || true
  if [ -d /run/systemd/system ]; then systemctl start --no-block nounoursos-instantanes.service >/dev/null 2>&1 || true; fi
  # Curseur NounoursOS par défaut, aussi pour les applications hors KDE
  update-alternatives --install /usr/share/icons/default/index.theme x-cursor-theme \
    /usr/share/icons/NounoursOS/cursor.theme 95 >/dev/null 2>&1 || true
  # Capsule temporelle : minuteur prêt pour chaque compte (il ne fait rien tant qu'elle est désactivée)
  systemctl --global enable nounoursos-capsule.timer >/dev/null 2>&1 || true
  # Identité NounoursOS : polices Inter pour le menu de démarrage
  T=/usr/share/grub/themes/nounoursos; F=/usr/share/fonts/opentype/inter
  if command -v grub-mkfont >/dev/null && [ -f "$F/Inter-Regular.otf" ] && [ -d "$T" ]; then
    grub-mkfont -s 16 -n "Inter" -o "$T/inter_16.pf2" "$F/Inter-Regular.otf" 2>/dev/null || true
    grub-mkfont -s 16 -n "Inter Fort" -o "$T/inter_fort_16.pf2" "$F/Inter-SemiBold.otf" 2>/dev/null || true
    grub-mkfont -s 30 -n "Inter Fort" -o "$T/inter_fort_30.pf2" "$F/Inter-Bold.otf" 2>/dev/null || true
    if [ -d /boot/grub ] && command -v update-grub >/dev/null; then update-grub >/dev/null 2>&1 || true; fi
  fi
  # Écran de démarrage : nouveau logo (seulement s'il a changé)
  P=/usr/share/plymouth/themes/nounoursos
  if [ -d "$P" ] && ! cmp -s /usr/share/nounoursos/plymouth/watermark.png "$P/watermark.png"; then
    cp /usr/share/nounoursos/plymouth/watermark.png "$P/watermark.png"
    cp /usr/share/nounoursos/plymouth/nounoursos.plymouth "$P/nounoursos.plymouth"
    if command -v update-initramfs >/dev/null && [ -d /boot ]; then update-initramfs -u >/dev/null 2>&1 || true; fi
  fi
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
log "nounoursos-minecraft $DESKTOP_VERSION"
P="$WORK/nounoursos-minecraft"
C="$ISO/common/includes.chroot"
mkdir -p "$P/DEBIAN"
take "$P" "$C" "usr/bin/nounoursos-minecraft"
take "$P" "$C" "usr/lib/nounoursos/python/nounours_minecraft.py"
chmod 755 "$P/usr/bin/nounoursos-minecraft"
cat > "$P/DEBIAN/control" <<EOF
Package: nounoursos-minecraft
Version: ${DESKTOP_VERSION}
Architecture: all
Maintainer: ${MAINTAINER}
Installed-Size: @SIZE@
Section: games
Priority: optional
Depends: python3, systemd
Suggests: openjdk-21-jre-headless | openjdk-25-jre-headless
Homepage: https://nounourscorp.fr/
Description: Serveur Minecraft (Paper) en un clic pour NounoursOS
 Télécharge Paper depuis PaperMC (empreinte vérifiée), le fait tourner comme service
 systemd, avec console RCON et sauvegardes du monde. Commande : nounoursos-minecraft.
EOF
build "$P"

# -----------------------------------------------------------------------------
log "nounoursos-server $DESKTOP_VERSION"
P="$WORK/nounoursos-server"
S="$ISO/server/includes.chroot"
mkdir -p "$P/DEBIAN"
take "$P" "$S" "usr/share/cockpit/nounoursos"
take "$P" "$S" "usr/share/cockpit/branding/nounoursos"
take "$P" "$S" "usr/libexec/nounoursos/nounoursos-roles"
chmod 755 "$P/usr/libexec/nounoursos/nounoursos-roles"
cat > "$P/DEBIAN/control" <<EOF
Package: nounoursos-server
Version: ${DESKTOP_VERSION}
Architecture: all
Maintainer: ${MAINTAINER}
Installed-Size: @SIZE@
Section: admin
Priority: optional
Depends: nounoursos-release, nounoursos-minecraft, cockpit-ws, cockpit-system, cockpit-bridge, curl, gpg
Recommends: cockpit-packagekit, ufw
Homepage: https://nounourscorp.fr/
Description: Tableau de bord NounoursOS Server (Cockpit)
 Cockpit aux couleurs NounoursOS (https://<serveur>:9090) avec une page NounoursOS :
 site web (Apache, PHP, MariaDB), Jellyfin et Minecraft (Paper) en un clic.
EOF
cat > "$P/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
  # Tableau de bord accessible depuis le réseau local (port 9090, connexion chiffrée)
  if command -v ufw >/dev/null; then ufw allow 9090/tcp >/dev/null 2>&1 || true; fi
  systemctl enable cockpit.socket >/dev/null 2>&1 || true
  if [ -d /run/systemd/system ]; then systemctl start cockpit.socket >/dev/null 2>&1 || true; fi
fi
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
# Applications tierces copiées depuis leurs Releases GitHub (dernière version) :
# préinstallées dans l'ISO et mises à jour via « Mise à jour de NounoursOS ».
# Non bloquant : si une appli n'est pas récupérable, le dépôt est publié sans elle.
log "Applications (dernières versions)"
M="$ROOT/scripts/miroir-github.py"
python3 "$M" winboat-org/winboat '-amd64\.deb$' winboat "$OUT" \
  || python3 "$M" TibixDev/winboat '-amd64\.deb$' winboat "$OUT" || true
python3 "$M" AngelGitHub17/Nounours-Launcher '_amd64\.deb$' nounours-launcher "$OUT" || true
# Partage façon AirDrop avec iPhone, Mac, Windows, Android
python3 "$M" localsend/localsend 'linux-x86-64\.deb$' localsend "$OUT" || true
# Dépôt privé : jeton dédié (secret NOUNOURS_BROWSER_TOKEN)
TOKEN_VAR=BROWSER_TOKEN python3 "$M" AngelGitHub17/Nounours-Browser '_amd64\.deb$' nounours-browser "$OUT" || true

log "Paquets prêts :"
ls -1 "$OUT"
