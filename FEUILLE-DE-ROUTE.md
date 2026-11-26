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

## 1.3 « Origami » ✅

- Nouvelle identité : ourson origami, fonds à facettes, police Inter, écran de connexion SDDM, écran de chargement, Plymouth, GRUB, installateur
- Mises à jour : recherche via `nounoursos-maj-recherche` (pkexec sans mot de passe), bornée et expliquée
- Capsule temporelle (rsync + liens durs, rétention façon Time Machine), recherche `Alt+Espace` avec réglages et actions, Mode jeu, Téléphone (KDE Connect), Nettoyage

## 1.4 « Miel » ✅

- Centre de contrôle (plasmoïde), modes Concentration (Ne pas déranger, applis, fond, horaires)
- Venir de Windows (fichiers + favoris), Retour en arrière (Btrfs + Snapper, installateur en Btrfs par défaut)
- Aperçu rapide (clic droit dans Dolphin), partage LocalSend, widgets Météo (Open-Meteo) et Agenda (.ics)
- NounoursAccount (assistant + Paramètres), serveur Minecraft Paper en 1 clic, kit streamer OBS
- Curseur NounoursOS et nouveaux sons
- Server : Cockpit aux couleurs NounoursOS, rôles Web (PHP/MariaDB), Jellyfin, Minecraft
- *Reporté : démarrer sur un instantané depuis le menu de démarrage (grub-btrfs n'est pas dans Debian 13), aperçu avec la barre d'espace dans Dolphin, synchronisation des préférences NounoursAccount, multidiffusion sans service tiers*

## 1.5 🔜

| Fonction | Détail |
|---|---|
| **Démarrer sur un instantané** | Entrées du menu de démarrage pour les instantanés (grub-btrfs ou équivalent) |
| **NounoursAccount** | Préférences synchronisées entre machines (fond, teinte, dispositions) |
| **Aperçu à la barre d'espace** | Raccourci dans Dolphin |

## LiberNT et NounoursNT ✅ (aperçu)

- NounoursOS NT démarre LiberNT (système NT libre, projet indépendant) dans une fenêtre, en un clic
- NounoursNT : système NT de NounoursCorp basé sur les sources de LiberNT, aux couleurs NounoursOS, publié
  en aperçu de développement (Releases `nounoursnt-…`)

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
| **Installation automatique** | Installation sans questions (preseed) pour les machines virtuelles Proxmox |
| **Mises à jour sans surprise** | Rapport hebdomadaire et redémarrage programmé après les mises à jour du noyau |

## NounoursOS for POS et for POS Server 💡

| Édition | Détail |
|---|---|
| **NounoursOS for POS** | Poste de caisse : NounoursPOS en plein écran au démarrage, douchette, imprimante de tickets, tiroir-caisse |
| **NounoursOS for POS Server** | Serveur de magasin : base NounoursPOS, stocks et ventes de toutes les caisses, multi-magasin |

## Plus tard 💡

- Passage à Debian 14 « Forky » avec assistant de mise à niveau (NounoursOS 2.0)
- Version ARM (Raspberry Pi 5)
