# 🐻 Feuille de route NounoursOS

Légende : ✅ fait · 🔜 prochaine version · 💡 idée à creuser

## 1.0 « Guimauve » ✅

- ISO bureau (KDE Plasma 6, dispositions Classique / Mac) et ISO Server
- Paramètres simplifiés, assistant de bienvenue, Mise à jour de NounoursOS
- Dépôt APT signé sur GitHub Pages, ISO construites par GitHub Actions
- **WinBoat préinstallé** : applications Windows dans des fenêtres NounoursOS
  (Docker, FreeRDP 3, groupe `docker`, page *Paramètres › Applications Windows*)

## 1.1 « Calinou » ✅

- NounoursLauncher et NounoursBrowser préinstallés (NounoursBrowser par défaut), mis à jour par le dépôt
- Logithèque : Flatpak + Flathub dans Discover, sélection NounoursCorp dans l'assistant
- Menu de démarrage (ISO et système installé) et écran de verrouillage NounoursOS
- Thème de sons NounoursOS
- *Reporté : curseur NounoursOS (à dessiner) ; ISO bureau sous 2 Go (2,8 Go avec WinBoat, Docker et les applis NounoursCorp : il faudrait retirer des firmwares ou des applis)*

## 1.2 « Doudou » ✅

- **Édition NounoursOS NT** : noyau trixie-backports (ntsync), Wine (WineHQ stable), `.exe`/`.msi` en double-clic, paquet `nounoursos-nt`
- Écran de veille animé (`nounoursos-veille`, swayidle), widgets Horloge et Moniteur
- Empreinte digitale (fprintd + PAM) ; *visage reporté : Howdy n'est pas empaqueté pour Debian 13*
- 6 teintes (schémas KDE clair/sombre + fonds assortis), fond d'écran animé QML
- Paramètres tout-en-un (pont KCM), icônes NounoursOS, mises à jour par APT (pkexec)

## 1.3 🔜 — Confort façon macOS

| Fonction | Détail |
|---|---|
| **Capsule temporelle** (sauvegarde) | Instantanés automatiques du système (Btrfs + Snapper, ou Timeshift) et retour en arrière depuis Paramètres et le menu de démarrage |
| **Recherche « Spotlight »** | `Alt+Espace` : KRunner restylé NounoursOS (applis, fichiers, calculs, réglages) |
| **Centre de contrôle** | Panneau de réglages rapides (Wi-Fi, son, luminosité, Ne pas déranger) dans la barre |
| **Compte NounoursAccount** | Connexion avec NounoursAccount dans l'assistant de bienvenue (photo, nom, préférences synchronisées) |
| **Kit streamer** | Option dans l'assistant : OBS Studio préconfiguré (multistream Twitch / YouTube / Kick) |
| **Mode jeu** | Steam, GameMode et pilotes graphiques en un clic depuis Paramètres |

## NounoursOS NT 💡

| Fonction | Détail |
|---|---|
| **Wine avec ntsync** | Wine compilé avec ntsync (le Wine de WineHQ ne l'utilise pas encore ; Proton-GE si) |
| **Bouteilles par logiciel** | Un préfixe Wine par programme, géré depuis Paramètres (façon Bottles) |
| **Raccourcis automatiques** | Les programmes installés apparaissent dans le menu et le dock avec leur icône |
| **Visage** | Déverrouillage par webcam infrarouge (Howdy ou équivalent quand il sera empaqueté) |

## NounoursOS Server 💡

| Fonction | Détail |
|---|---|
| **Tableau de bord web** | Cockpit aux couleurs NounoursOS pour gérer le serveur depuis un navigateur |
| **Rôles prêts à l'emploi** | Serveur Minecraft (Paper), Jellyfin, serveur web PHP/MySQL… installés et configurés en une commande |
| **Installation automatique** | Installation sans questions (preseed) pour les machines virtuelles Proxmox |
| **Mises à jour sans surprise** | Rapport hebdomadaire et redémarrage programmé après les mises à jour du noyau |

## Plus tard 💡

- Passage à Debian 14 « Forky » avec assistant de mise à niveau (NounoursOS 2.0)
- Version ARM (Raspberry Pi 5)
- Lien avec l'iPhone (KDE Connect : notifications, fichiers, presse-papiers)
