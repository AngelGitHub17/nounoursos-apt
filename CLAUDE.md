# CLAUDE.md — NounoursOS

Distribution Linux de **NounoursCorp** basée sur **Debian 13 « Trixie »**.
Trois éditions : **NounoursOS** (`desktop`, KDE Plasma 6), **NounoursOS NT** (`nt`, bureau + couche Windows),
**NounoursOS Server** (`server`). Version actuelle : voir `iso/VERSION` (1.2 « Doudou »).

Tout est en **français** : interface, commentaires, messages de commit, notes de version.

## Règles

- **sudo** : c'est toujours l'utilisateur qui tape son mot de passe dans un terminal. Ne jamais le saisir soi-même.
- **Jamais de secret dans le dépôt** : la clé GPG privée (`cle-privee-*.asc`, ignorée par git) vit uniquement dans
  le secret GitHub `GPG_PRIVATE_KEY` ; le jeton du dépôt privé NounoursBrowser dans `NOUNOURS_BROWSER_TOKEN`.
- Commits : auteur `DidiKaria`, e-mail `74068022+AngelGitHub17@users.noreply.github.com`.
- Tester ce qui peut l'être avant de pousser (voir « Tester »). Une ISO ratée coûte 1 h de CI.
- Hooks live-build : `#!/bin/sh` compatible **dash**, `set -e`, `DEBIAN_FRONTEND=noninteractive`.
- Paquets dans `config/packages.chroot` : nommés `nom_version_arch.deb`, sinon live-build les ignore.

## Organisation

```
iso/
  VERSION                 VERSION, CODENAME, DEBIAN_BASE (source unique)
  build.sh                sudo ./build.sh desktop|server|nt
  common/ desktop/ server/ Couches live-build (package-lists, hooks/live, includes.chroot)
  nt/                     Posée par-dessus desktop/ : pin noyau backports, Wine, nounoursos-exe
  assets/                 Générateurs : icones.py (icônes Paramètres), make-themes.py (teintes + fonds)
  bootloaders/splash.svg  Menu de démarrage de l'ISO
  outils/                 fusionner-iso.bat / .sh (ISO > 2 Gio découpée)
scripts/
  construire-paquets.sh   .deb : nounoursos-release, -desktop, -nt, -archive-keyring (+ miroirs)
  miroir-github.py        Copie les .deb des Releases (winboat, nounours-launcher, nounours-browser)
src/kcm-pont/             Pont C++ : modules KDE (KCM) affichés DANS Paramètres
nouveautes/X.Y.md         Notes de version (affichées dans Mise à jour et la Release)
.github/workflows/        publier.yml (dépôt APT → GitHub Pages), iso.yml (ISO → Releases)
```

Applications PyQt6 : `iso/desktop/includes.chroot/usr/lib/nounoursos/python/nounoursui/`
(`parametres`, `bienvenue`, `maj`, `veille`, `kcm`, `updates`). Helper root :
`usr/libexec/nounoursos/nounoursos-root-helper` via pkexec (action polkit `fr.nounourscorp.nounoursos.root-helper`).

## Mises à jour

- Dépôt APT signé sur GitHub Pages (`AngelGitHub17/nounoursos-apt`), reconstruit à chaque push et chaque nuit.
- `nounoursos-release` (version = `iso/VERSION`) = nouvelle version du système ; il garde l'édition installée.
- `nounoursos-desktop` / `nounoursos-nt` : version `VERSION+git<nb de commits>`, change à chaque commit.
- Un fichier ajouté dans `includes.chroot` doit aussi être ajouté à la liste `take` du bon paquet
  dans `construire-paquets.sh`, sinon les machines installées ne le reçoivent jamais.

## Tester

- Paramètres hors machine : `QT_QPA_PLATFORM=offscreen NOUNOURSOS_DEMO=1 NOUNOURSOS_ROOT=<racine copiée>`.
- Écran de veille : `NOUNOURSOS_VEILLE_DEMO=1|erreur|chaud nounoursos-veille --fenetre`.
- Plasmoïdes : `plasmoidviewer -a org.nounoursos.horloge` (conteneur debian:trixie + plasma-sdk + Xvfb).
- Fond animé : charger `contents/ui/Fond.qml` dans un QQuickView (il n'a pas besoin de Plasma).
- Paquets : `SANS_MIROIRS=1 bash scripts/construire-paquets.sh` puis `dpkg-deb -c dist/…`.
- JS des dispositions : `node --check …/desktop-layout.js`.

## Tâches

### Fait (1.2 « Doudou »)
- [x] Écran de veille animé (`nounoursos-veille` + swayidle, page Paramètres)
- [x] Widgets bureau Horloge + Moniteur (ksystemstats), placés par les dispositions, interrupteurs dans Bureau et Dock
- [x] Empreinte digitale (fprintd, `pam-auth-update`, enregistrement dans Paramètres)
- [x] 6 teintes (schémas KDE clair/sombre + fonds assortis) et fond d'écran animé `org.nounoursos.fond`
- [x] Édition NounoursOS NT : noyau backports (ntsync), WineHQ stable, `.exe`/`.msi` en double-clic
- [x] Paramètres tout-en-un (pont KCM), icônes NounoursOS, mises à jour par APT

### À faire
- [ ] Construire les 3 ISO 1.2 en CI, les tester en VM (NT : vérifier `/dev/ntsync` et un `.exe`), publier la Release
- [ ] Reconnaissance du visage (attendre un Howdy empaqueté pour Debian 13)
- [ ] NT : Wine avec ntsync, un préfixe par programme, raccourcis automatiques dans le menu
- [ ] Fond animé : se mettre en pause quand une fenêtre couvre tout l'écran
- [ ] Curseur NounoursOS (à dessiner)
- [ ] 1.3 : capsule temporelle (Snapper), recherche façon Spotlight, centre de contrôle, NounoursAccount dans l'assistant, kit streamer OBS, mode jeu
- [ ] Server : tableau de bord Cockpit NounoursOS, rôles (Minecraft Paper, Jellyfin, web PHP/MySQL), preseed Proxmox
- [ ] 2.0 : Debian 14 « Forky » avec assistant de mise à niveau
