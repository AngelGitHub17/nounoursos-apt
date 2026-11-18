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
- ISO bureau allégée (firmwares non dupliqués)
- *Reporté : curseur NounoursOS (à dessiner)*

## 1.2 🔜 — Confort façon macOS

| Fonction | Détail |
|---|---|
| **Capsule temporelle** (sauvegarde) | Instantanés automatiques du système (Btrfs + Snapper, ou Timeshift) et retour en arrière depuis Paramètres et le menu de démarrage |
| **Recherche « Spotlight »** | `Alt+Espace` : KRunner restylé NounoursOS (applis, fichiers, calculs, réglages) |
| **Centre de contrôle** | Panneau de réglages rapides (Wi-Fi, son, luminosité, Ne pas déranger) dans la barre |
| **Compte NounoursAccount** | Connexion avec NounoursAccount dans l'assistant de bienvenue (photo, nom, préférences synchronisées) |
| **Kit streamer** | Option dans l'assistant : OBS Studio préconfiguré (multistream Twitch / YouTube / Kick) |
| **Mode jeu** | Steam, GameMode et pilotes graphiques en un clic depuis Paramètres |

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
