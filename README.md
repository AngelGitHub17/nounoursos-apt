# 🐻 NounoursOS

Distribution Linux de **NounoursCorp**, basée sur Debian 13 « Trixie ».
Ce dépôt contient **tout** NounoursOS :

| Dossier | Contenu |
|---|---|
| [`iso/`](iso/) | Construction des ISO (bureau et Server) avec live-build — voir [`iso/README.md`](iso/README.md) |
| [`scripts/`](scripts/) | Fabrication des paquets `.deb` et du dépôt APT signé |
| [`nouveautes/`](nouveautes/) | Texte « Quoi de neuf » de chaque version, affiché dans *Mise à jour de NounoursOS* |
| [`.github/workflows/publier.yml`](.github/workflows/publier.yml) | Publication automatique du dépôt sur GitHub Pages |
| [`depot.conf`](depot.conf) | Adresse du dépôt (à changer si tu passes sur un domaine perso) |

Dépôt APT publié : **https://angelgithub17.github.io/nounoursos-apt**

## Comment les mises à jour arrivent sur les machines

```
 tu modifies iso/… ──push──▶ GitHub Actions ──▶ paquets .deb signés ──▶ GitHub Pages
                                                                          │
   Mise à jour de NounoursOS ◀── apt / PackageKit (toutes les 4 h) ◀──────┘
```

| Paquet | Contient | Version |
|---|---|---|
| `nounoursos-release` | Identité du système (`/etc/os-release`) | `iso/VERSION` → ne change que pour une **nouvelle version** de NounoursOS |
| `nounoursos-desktop` | Applis NounoursOS, thème, fonds d'écran, icônes | `VERSION+gitN` → change à **chaque** publication |
| `nounoursos-archive-keyring` | Clé de signature + adresse du dépôt | fixe |

- Un simple push (correction d'une appli, nouveau fond d'écran…) → les machines voient
  « **Mise à jour de NounoursOS 1.0** disponible ».
- Passer `VERSION=1.1` dans `iso/VERSION` + écrire `nouveautes/1.1.md` → les machines voient
  « **NounoursOS 1.1 est disponible** » avec le texte des nouveautés, façon macOS.

## Mise en route (une seule fois)

1. **Activer GitHub Pages** : *Settings → Pages → Build and deployment → Source :* **GitHub Actions**.
2. **Créer la clé de signature** (sur ta VM Debian ou ton Mac, avec `gpg`) :
   ```bash
   git clone https://github.com/AngelGitHub17/nounoursos-apt && cd nounoursos-apt
   ./scripts/creer-cle.sh
   ```
   Le script crée `nounoursos.asc` (publique) et `cle-privee-NE-PAS-PARTAGER.asc` (privée).
3. **Mettre la clé privée dans GitHub** : *Settings → Secrets and variables → Actions →
   New repository secret* — nom `GPG_PRIVATE_KEY`, valeur = tout le fichier privé.
   (Le script le fait tout seul si la commande `gh` est installée et connectée.)
4. **Sauvegarder la clé privée** (gestionnaire de mots de passe, clé USB…) puis la supprimer
   du dossier. ⚠️ Si elle est perdue, il faudra changer la clé sur toutes les machines.
5. **Committer la clé publique** : `git add nounoursos.asc && git commit -m "Clé publique" && git push`
   → l'Action se lance et publie le dépôt (onglet *Actions* pour suivre).

À partir de là, `iso/build.sh` détecte le dépôt en ligne et l'intègre aux ISO.

## Publier une nouvelle version de NounoursOS

```bash
# 1. numéro et nom
sed -i 's/^VERSION=.*/VERSION=1.1/; s/^CODENAME=.*/CODENAME="Aurore"/' iso/VERSION
# 2. le texte « Quoi de neuf » (Markdown)
nano nouveautes/1.1.md
# 3. publier
git commit -am "NounoursOS 1.1" && git push
```

## Construire les ISO sur GitHub

Onglet **Actions → Construire les ISO NounoursOS → Run workflow** (édition, et case
« Publier une Release » si tu veux une page de téléchargement publique).
Compter 40 à 90 min. Les ISO sont dans le run (section *Artifacts*), et dans
**Releases** si publiées. Pousser un tag publie automatiquement :

```bash
git tag v1.0 && git push origin v1.0
```

GitHub limite chaque fichier de Release à 2 Gio : si l'ISO est plus grosse, elle est
découpée en `.part0`, `.part1`… (la page de la Release explique comment les recoller).

## Tester en local

```bash
./scripts/construire-paquets.sh   # → dist/*.deb
./scripts/construire-depot.sh     # → public/ (nécessite une clé GPG privée importée)
```
