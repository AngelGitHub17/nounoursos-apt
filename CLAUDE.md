# CLAUDE.md — NounoursOS

Distribution Linux de **NounoursCorp** basée sur **Debian 13 « Trixie »**.
Trois éditions : **NounoursOS** (`desktop`, KDE Plasma 6), **NounoursOS NT** (`nt`, bureau + couche Windows),
**NounoursOS Server** (`server`). Version actuelle : voir `iso/VERSION` (1.3 « Origami »).

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
  assets/                 Générateurs : identite.py (logo, fonds, GRUB, Plymouth, SDDM, installateur, ISO),
                          icones.py (icônes Paramètres), make-themes.py (teintes + fonds assortis)
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
(`parametres`, `bienvenue`, `maj`, `veille`, `kcm`, `updates`, `capsule`).

## Identité

- Ourson **origami** (facettes), miel `#D98A3F` / `#F5B862` sur prune nuit `#1B1329`, police **Inter**,
  signature « Doux dehors, solide dedans. ». Tout est généré par `iso/assets/identite.py` : ne jamais
  retoucher les PNG à la main, modifier le générateur puis le relancer. Helper root :
`usr/libexec/nounoursos/nounoursos-root-helper` via pkexec (action polkit `fr.nounourscorp.nounoursos.root-helper`).

## Mises à jour

- Recherche : `nounoursos-maj-recherche` via pkexec, **sans mot de passe** (action polkit
  `maj-rechercher`, programme dédié : pkexec choisit l'action par le chemin du programme).
  Pas de PackageKit pour rafraîchir (il pouvait attendre sans fin derrière un autre outil APT).
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
- Recherche : lancer `nounoursos-recherche` dans `dbus-run-session`, puis
  `gdbus call --session -d fr.nounourscorp.Recherche -o /recherche -m org.kde.krunner1.Match wifi`.
- Écran de connexion : `sddm-greeter-qt6 --test-mode --theme …/sddm/themes/nounoursos` sous Xvfb.
- Capsule : `HOME=<faux dossier> python3` + `nounoursui.capsule.sauvegarder()`, vérifier les liens durs.

## Tâches

### Fait (1.2 « Doudou »)
- [x] Écran de veille animé (`nounoursos-veille` + swayidle, page Paramètres)
- [x] Widgets bureau Horloge + Moniteur (ksystemstats), placés par les dispositions, interrupteurs dans Bureau et Dock
- [x] Empreinte digitale (fprintd, `pam-auth-update`, enregistrement dans Paramètres)
- [x] 6 teintes (schémas KDE clair/sombre + fonds assortis) et fond d'écran animé `org.nounoursos.fond`
- [x] Édition NounoursOS NT : noyau backports (ntsync), WineHQ stable, `.exe`/`.msi` en double-clic
- [x] Paramètres tout-en-un (pont KCM), icônes NounoursOS, mises à jour par APT

### Fait (1.3 « Origami »)
- [x] Nouvelle identité (ourson origami, Inter, SDDM, ksplash, Plymouth, GRUB, Calamares, ISO)
- [x] Mises à jour : recherche fiable (pkexec sans mot de passe, délais bornés, erreurs expliquées)
- [x] Capsule temporelle, recherche Alt+Espace (module KRunner D-Bus), Mode jeu, Téléphone, Nettoyage

### À faire
- [ ] Tester les ISO 1.3 en VM : connexion SDDM, Capsule sur disque USB, recherche, NT (`/dev/ntsync`, un `.exe`)
- [ ] Reconnaissance du visage (attendre un Howdy empaqueté pour Debian 13)
- [ ] NT : Wine avec ntsync, un préfixe par programme, raccourcis automatiques dans le menu
- [ ] Fond animé : se mettre en pause quand une fenêtre couvre tout l'écran
- [ ] Curseur NounoursOS (à dessiner)
- [ ] 1.4 : instantanés du système (Btrfs + Snapper), centre de contrôle, NounoursAccount dans l'assistant, kit streamer OBS
- [ ] Server : tableau de bord Cockpit NounoursOS, rôles (Minecraft Paper, Jellyfin, web PHP/MySQL), preseed Proxmox
- [ ] 2.0 : Debian 14 « Forky » avec assistant de mise à niveau
