#!/usr/bin/env bash
# =============================================================================
#  Construit le dépôt APT signé dans public/ (publié ensuite sur GitHub Pages)
#  Prérequis : ./scripts/construire-paquets.sh, une clé GPG privée importée,
#              apt-ftparchive (paquet apt-utils).
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=/dev/null
. "$ROOT/depot.conf"
# shellcheck source=/dev/null
. "$ROOT/iso/VERSION"
PUB="$ROOT/public"
DIST="dists/$SUITE"

KEYID=$(gpg --list-secret-keys --with-colons | awk -F: '/^fpr:/ {print $10; exit}')
[ -n "$KEYID" ] || { echo "❌ Pas de clé GPG privée (secret GPG_PRIVATE_KEY ?)" >&2; exit 1; }

rm -rf "$PUB"
mkdir -p "$PUB/pool/$COMPONENT" "$PUB/$DIST/$COMPONENT/binary-amd64"
cp "$ROOT"/dist/*.deb "$PUB/pool/$COMPONENT/"

cd "$PUB"
apt-ftparchive packages "pool/$COMPONENT" > "$DIST/$COMPONENT/binary-amd64/Packages"
gzip -9kn "$DIST/$COMPONENT/binary-amd64/Packages"
xz -9k "$DIST/$COMPONENT/binary-amd64/Packages"

apt-ftparchive \
  -o APT::FTPArchive::Release::Origin="NounoursCorp" \
  -o APT::FTPArchive::Release::Label="NounoursOS" \
  -o APT::FTPArchive::Release::Suite="$SUITE" \
  -o APT::FTPArchive::Release::Codename="$SUITE" \
  -o APT::FTPArchive::Release::Architectures="amd64" \
  -o APT::FTPArchive::Release::Components="$COMPONENT" \
  -o APT::FTPArchive::Release::Description="Dépôt NounoursOS ${VERSION}" \
  release "$DIST" > /tmp/Release.nounoursos
mv /tmp/Release.nounoursos "$DIST/Release"

gpg --batch --yes --local-user "$KEYID" --clearsign -o "$DIST/InRelease" "$DIST/Release"
gpg --batch --yes --local-user "$KEYID" --armor --detach-sign -o "$DIST/Release.gpg" "$DIST/Release"
gpg --armor --export "$KEYID" > nounoursos.asc

# Notes de version (affichées par « Mise à jour de NounoursOS »)
mkdir -p nouveautes
cp "$ROOT"/nouveautes/*.md nouveautes/ 2>/dev/null || true

# Page d'accueil du dépôt
PKGS=$(apt-ftparchive packages "pool/$COMPONENT" | awk '/^Package:/ {p=$2} /^Version:/ {printf "<li><code>%s</code> %s</li>", p, $2}')
sed -e "s|@URL@|$URL|g" -e "s|@SUITE@|$SUITE|g" -e "s|@VERSION@|$VERSION|g" \
    -e "s|@CODENAME@|$CODENAME|g" -e "s|@PKGS@|$PKGS|g" "$ROOT/scripts/index.html.in" > index.html
cp "$ROOT/iso/common/includes.chroot/usr/share/nounoursos/logo-256.png" logo.png
touch .nojekyll

echo "🐻 Dépôt prêt dans public/ (clé $KEYID)"
