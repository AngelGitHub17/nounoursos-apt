# 🐻 NounoursOS

Distribution Linux de **NounoursCorp**, basée sur **Debian 13 « Trixie »**.

| Édition | Contenu | Installateur |
|---|---|---|
| **NounoursOS** (`desktop`) | KDE Plasma 6, deux dispositions au choix : **Classique** ou **Mac** (barre de menus + dock) | Calamares (graphique) |
| **NounoursOS Server** (`server`) | Console uniquement, SSH, pare-feu ufw, fail2ban, mises à jour de sécurité automatiques | Debian-Installer (texte) |

Version actuelle : **1.0 « Guimauve »** (modifiable dans `VERSION`).

---

## 1. Préparer la machine de build

Il faut une **Debian 13** (VM ou physique). Sur ton Proxmox :

- VM Debian 13 (netinst), **4 vCPU, 4 à 8 Go de RAM, 40 Go de disque**
- Installation minimale + SSH, pas besoin de bureau
- Si Debian a été installée **depuis le DVD**, APT pointe encore vers le DVD : à corriger d'abord (en root, via `su -`) :

```bash
sed -i 's/^deb cdrom:/# deb cdrom:/' /etc/apt/sources.list
cat > /etc/apt/sources.list.d/debian.sources <<'EOF'
Types: deb
URIs: http://deb.debian.org/debian
Suites: trixie trixie-updates
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: http://security.debian.org/debian-security
Suites: trixie-security
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
EOF
apt update
```

- Puis :

```bash
apt install -y live-build git sudo
```

> Utilise `su -` (avec le tiret) et non `su` : sinon `/usr/sbin` n'est pas dans le PATH
> et live-build ne trouve pas certains outils. Ou ajoute ton compte au groupe sudo :
> `usermod -aG sudo dream` puis déconnexion/reconnexion.

> ⚠️ Fais le build dans une **VM**, pas dans un conteneur LXC : live-build a besoin de
> monter des systèmes de fichiers (proc, sys…) et ça coince en LXC non privilégié.

## 2. Construire

Récupérer le projet : `git clone https://github.com/AngelGitHub17/nounoursos-apt && cd nounoursos-apt/iso`
(ensuite `git pull` pour les mises à jour du projet).


```bash
cd nounoursos
sudo ./build.sh desktop     # → out/NounoursOS-desktop-1.0-amd64.iso
sudo ./build.sh server      # → out/NounoursOS-server-1.0-amd64.iso
```

- 1ᵉʳ build : **30 à 60 min** (téléchargement de ~2 Go de paquets).
- Builds suivants : bien plus rapides, le cache des paquets est conservé.
- Repartir de zéro : `sudo CLEAN=1 ./build.sh desktop`
- En cas d'erreur, tout est dans `build/<édition>/build.log`
  (cherche les lignes `E:` ou `[NounoursOS]` pour savoir quel hook a planté).

## 3. Tester l'ISO

- **Proxmox** : upload de l'ISO dans le stockage, nouvelle VM, BIOS **OVMF (UEFI)**
  pour tester comme sur un vrai PC récent (et SeaBIOS pour tester l'ancien mode BIOS).
- **PC Windows** : VirtualBox ou Hyper-V, 4 Go de RAM mini.
- **Vraie machine** : copie l'ISO sur une clé USB avec Rufus (mode DD) ou Balena Etcher.
- **Mac Apple Silicon** : l'ISO est en amd64, UTM l'émule mais c'est très lent → préfère Proxmox.

En live : utilisateur `nounours`, mot de passe `live`.

### Check-list de test (édition bureau)

- [ ] Écran de démarrage NounoursOS (logo ours + barre couleur miel)
- [ ] Session live ouverte automatiquement, fond d'écran NounoursOS
- [ ] Fenêtre « Bienvenue » → bouton « Installer NounoursOS »
- [ ] Icône « Installer NounoursOS » sur le bureau, pas de « Install Debian »
- [ ] Installateur aux couleurs NounoursOS, diaporama pendant l'installation
- [ ] Après installation : GRUB affiche « NounoursOS »
- [ ] Premier login : choix Classique / Mac, puis bascule possible via le menu « Disposition NounoursOS »
- [ ] Centre d'infos (kinfocenter) : « NounoursOS 1.0 (Guimauve) » avec le logo
- [ ] `cat /etc/os-release` → NounoursOS ; `sudo apt upgrade` ne remet pas « Debian »

---

## 4. Organisation du projet

```
nounoursos/
├── build.sh                 Script de build (desktop | server)
├── VERSION                  Numéro et nom de version (source unique)
├── assets/                  Sources SVG : logo, fond d'écran
├── common/                  Partagé par les 2 éditions
│   ├── package-lists/       Paquets de base, firmwares
│   ├── hooks/live/          Branding système (os-release, locale FR…)
│   └── includes.chroot/     Fichiers copiés tels quels dans le système (icônes, GRUB)
├── desktop/                 Édition bureau
│   ├── package-lists/       KDE Plasma + applis
│   ├── hooks/live/          Plymouth, Calamares
│   └── includes.chroot/
│       ├── usr/share/plasma/look-and-feel/   Dispositions Classique et Mac
│       ├── usr/share/wallpapers/NounoursOS/  Fond d'écran
│       ├── etc/calamares/branding/nounoursos Installateur
│       └── usr/bin/nounoursos-*              Accueil + choix de disposition
└── server/                  Édition serveur (SSH, ufw, fail2ban, motd)
```

Principe live-build : `package-lists/*.list.chroot` = paquets installés,
`includes.chroot/` = fichiers copiés à la racine du système,
`hooks/live/*.hook.chroot` = scripts lancés dans le système à la fin.

## 5. Personnaliser

| Je veux… | Je modifie… |
|---|---|
| Ajouter/retirer un logiciel | `desktop/package-lists/nounoursos-desktop.list.chroot` |
| Changer le logo | `assets/logo.svg` puis régénérer les PNG (voir ci-dessous) |
| Changer le fond d'écran | `assets/wallpaper.svg` → PNG dans `desktop/includes.chroot/usr/share/wallpapers/NounoursOS/contents/images/` |
| Modifier le dock Mac | `…/look-and-feel/org.nounoursos.mac/contents/layouts/org.kde.plasma.desktop-layout.js` |
| Passer en version 1.1 | `VERSION` (et `strings:` dans `branding.desc`) |
| Ajouter des fichiers dans les dossiers perso | `desktop/includes.chroot/etc/skel/` |

Régénérer les icônes après modification du logo (`sudo apt install librsvg2-bin`) :

```bash
for s in 16 22 24 32 48 64 128 256 512; do
  rsvg-convert -w $s -h $s assets/logo.svg \
    -o common/includes.chroot/usr/share/icons/hicolor/${s}x${s}/apps/nounoursos.png
done
```

## 6. Choix techniques à connaître

- **os-release « détourné »** : `/usr/lib/os-release` appartient au paquet Debian `base-files`.
  Le hook utilise `dpkg-divert` pour qu'une mise à jour Debian ne l'écrase pas.
  `ID=nounoursos` + `ID_LIKE=debian` : la plupart des logiciels reconnaissent quand même
  une base Debian. Quelques scripts d'installation tiers testent `ID=debian` strictement ;
  dans ce cas, on passera à `ID=debian` (c'est ce que font certaines dérivées).
- **`bootloaderEntryName: "debian"`** dans Calamares : obligatoire pour que le GRUB signé
  de Debian démarre avec **Secure Boot**. Le nom affiché reste « NounoursOS ».
- **Mises à jour** : NounoursOS utilise directement les dépôts Debian. Tu profites donc de
  toutes les mises à jour de sécurité Debian sans rien faire.
- **SSH (Server)** : désactivé en session live (mot de passe connu), actif une fois installé.

## 7. Feuille de route

1. ✅ v1.0 : ISO bureau + serveur, branding, deux dispositions, installateur
2. Dépôt APT NounoursCorp (`apt.nounourscorp.fr`) signé avec une clé GPG
3. Paquet `nounoursos-branding` (.deb) : le branding passe dans un vrai paquet → mises à jour
   du thème via `apt upgrade` sur les machines déjà installées
4. Paquets `.deb` de NounoursLauncher, NounoursBrowser… préinstallés
5. Thème GRUB et menu de démarrage de l'ISO aux couleurs NounoursOS
6. Server : installation automatisée (preseed) et rôles prêts à l'emploi (web, Minecraft…)

## 8. Applications NounoursOS

Écrites en Python + PyQt6, dans `desktop/includes.chroot/usr/lib/nounoursos/python/nounoursui/`.

| Commande | Rôle |
|---|---|
| `nounoursos-parametres` | **Paramètres** façon macOS : Wi-Fi, Bluetooth, Son, Apparence, Fond d'écran, Bureau et Dock, Mise à jour, À propos. Les autres réglages ouvrent juste le module KDE concerné. La grosse « Configuration du système » KDE est cachée du menu, accessible via *Réglages avancés…* |
| `nounoursos-bienvenue` | **En live** : écran plein écran *Essayer / Installer*. **Après installation** : assistant de premier démarrage (Bonjour → apparence → disposition → mises à jour → prêt). `--force` pour le relancer. |
| `nounoursos-maj` | **Mise à jour de NounoursOS** : fenêtre façon macOS (maintenant ou au redémarrage). `--daemon` = service lancé à l'ouverture de session : vérifie toutes les 4 h, icône avec pastille + notification. |
| `nounoursos-installer` | Lance Calamares, quel que soit le nom du lanceur Debian. |

**Tester sans rien installer** (dans la session live par exemple) : `NOUNOURSOS_DEMO=1 nounoursos-maj`,
`NOUNOURSOS_DEMO=1 nounoursos-parametres`, `nounoursos-bienvenue --force --windowed --now`.

**Mises à jour** : elles passent par PackageKit (`pkcon`). Les correctifs de sécurité Debian
s'installent tout seuls (unattended-upgrades, désactivable dans Paramètres). Pour annoncer une
**nouvelle version de NounoursOS** (« NounoursOS 1.1 est disponible »), il suffira de publier
un paquet `nounoursos-release` en version 1.1 dans le futur dépôt APT NounoursCorp :
la fenêtre de mise à jour le détecte et l'affiche comme une mise à jour système.
