// NounoursOS — disposition « Classique » pour Plasma 6
// Une barre flottante en bas, comme KDE par défaut, aux couleurs NounoursOS.

// --- Fond d'écran ------------------------------------------------------------
var desks = desktopsForActivity(currentActivity());
for (var i = 0; i < desks.length; i++) {
    desks[i].wallpaperPlugin = "org.kde.image";
    desks[i].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desks[i].writeConfig("Image", "file:///usr/share/wallpapers/NounoursOS/");
    // Widgets NounoursOS : horloge et moniteur, en haut à droite
    var geo = screenGeometry(desks[i].screen);
    var u = gridUnit;
    desks[i].addWidget("org.nounoursos.horloge", geo.width - 25 * u, 2 * u, 22 * u, 10 * u);
    desks[i].addWidget("org.nounoursos.moniteur", geo.width - 21 * u, (2 + 11) * u, 18 * u, 11 * u);
}

// --- Barre du bas --------------------------------------------------------------
var panel = new Panel;
panel.location = "bottom";
panel.height = Math.round(gridUnit * 2.6);
try { panel.floating = true; } catch (e) {}

var menu = panel.addWidget("org.kde.plasma.kickoff");
menu.currentConfigGroup = ["General"];
menu.writeConfig("icon", "nounoursos");

panel.addWidget("org.kde.plasma.pager");

var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:org.kde.dolphin.desktop",
    "preferred://browser",
    "applications:NounoursLauncher.desktop",
    "applications:org.kde.konsole.desktop",
    "applications:org.kde.discover.desktop",
    "applications:nounoursos-parametres.desktop"
]);

panel.addWidget("org.kde.plasma.marginsseparator");
panel.addWidget("org.nounoursos.controle");   // Centre de contrôle NounoursOS
panel.addWidget("org.kde.plasma.systemtray");
panel.addWidget("org.kde.plasma.digitalclock");
panel.addWidget("org.kde.plasma.showdesktop");
