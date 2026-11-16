#!/usr/bin/env bash
# =============================================================================
#  Crée la clé GPG qui signe le dépôt NounoursOS. À lancer UNE SEULE FOIS,
#  sur ton ordinateur (pas sur GitHub). Elle sert ensuite pendant des années.
#
#  Résultat :
#    - nounoursos.asc                    clé PUBLIQUE  -> à committer dans le dépôt
#    - cle-privee-NE-PAS-PARTAGER.asc    clé PRIVÉE    -> secret GitHub GPG_PRIVATE_KEY
#                                                         + sauvegarde (gestionnaire de mots de passe)
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f nounoursos.asc ]; then
  echo "⚠  nounoursos.asc existe déjà : une clé a déjà été créée."
  echo "   En recréer une obligerait toutes les machines installées à mettre à jour leur clé."
  read -r -p "Continuer quand même ? [o/N] " r; [ "$r" = "o" ] || exit 1
fi

TMP=$(mktemp -d)
export GNUPGHOME="$TMP"
chmod 700 "$TMP"

gpg --batch --passphrase '' --quick-gen-key \
  "NounoursOS - signature du depot <depot@nounourscorp.fr>" ed25519 sign 5y

FPR=$(gpg --list-keys --with-colons | awk -F: '/^fpr:/ {print $10; exit}')
gpg --armor --export "$FPR" > nounoursos.asc
gpg --armor --export-secret-keys "$FPR" > cle-privee-NE-PAS-PARTAGER.asc
chmod 600 cle-privee-NE-PAS-PARTAGER.asc
rm -rf "$TMP"

echo
echo "🐻 Clé créée : $FPR (valable 5 ans)"
echo
if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
  gh secret set GPG_PRIVATE_KEY < cle-privee-NE-PAS-PARTAGER.asc && echo "✅ Secret GPG_PRIVATE_KEY envoyé sur GitHub."
else
  echo "➡  Va sur GitHub : dépôt nounoursos-apt > Settings > Secrets and variables > Actions"
  echo "   > New repository secret. Nom : GPG_PRIVATE_KEY"
  echo "   Valeur : tout le contenu de cle-privee-NE-PAS-PARTAGER.asc (BEGIN … END compris)."
fi
echo
echo "➡  Ensuite :"
echo "   1. Sauvegarde cle-privee-NE-PAS-PARTAGER.asc dans un endroit sûr, puis supprime-la d'ici."
echo "   2. git add nounoursos.asc && git commit -m 'Clé publique du dépôt' && git push"
