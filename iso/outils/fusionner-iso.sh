#!/bin/sh
# =============================================================================
#  NounoursOS — recolle une ISO téléchargée en plusieurs morceaux (.part0, .part1…)
#  et vérifie qu'elle est intacte (empreinte SHA-256).
#
#  macOS / Linux : mets ce fichier dans le même dossier que les .part, puis
#                  dans un Terminal :   sh fusionner-iso.sh
# =============================================================================
cd "$(dirname "$0")" || exit 1

found=0
for first in *.iso.part0; do
  [ -e "$first" ] || continue
  found=1
  iso="${first%.part0}"
  echo "🐻 Fusion de $iso…"

  # Tous les morceaux doivent être là, sans trou dans la numérotation
  n=0
  while [ -e "$iso.part$n" ]; do n=$((n + 1)); done
  if [ -e "$iso.part$((n + 1))" ]; then
    echo "❌ Il manque $iso.part$n : télécharge tous les morceaux puis relance."
    exit 1
  fi

  i=0
  : > "$iso" || exit 1
  while [ "$i" -lt "$n" ]; do
    cat "$iso.part$i" >> "$iso" || { echo "❌ Erreur en lisant $iso.part$i"; exit 1; }
    i=$((i + 1))
  done
  echo "   $n morceaux assemblés."

  if [ -f "$iso.sha256" ]; then
    printf '   Vérification de l'"'"'intégrité… '
    if command -v sha256sum >/dev/null 2>&1; then
      sha256sum -c --quiet "$iso.sha256" >/dev/null 2>&1; ok=$?
    else
      shasum -a 256 -c "$iso.sha256" >/dev/null 2>&1; ok=$?
    fi
    if [ "$ok" -eq 0 ]; then
      echo "OK ✅"
      echo "   Tu peux supprimer les fichiers .part : $iso est prête."
    else
      echo "ÉCHEC ❌"
      echo "   L'ISO est abîmée : retélécharge les morceaux puis relance."
      rm -f "$iso"
      exit 1
    fi
  else
    echo "   (pas de fichier $iso.sha256 : intégrité non vérifiée)"
  fi
done

if [ "$found" -eq 0 ]; then
  echo "Aucun fichier .iso.part0 trouvé dans ce dossier."
  echo "Mets fusionner-iso.sh dans le même dossier que les morceaux téléchargés."
  exit 1
fi
