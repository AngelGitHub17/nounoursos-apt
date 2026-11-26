// NounoursOS — disposition « Mac » pour Plasma 6
// Barre en haut (menu NounoursOS, menu global, zone de notification, horloge)
// + dock flottant centré en bas.

// --- Fond d'écran ------------------------------------------------------------
var desks = desktopsForActivity(currentActivity());
for (var i = 0; i < desks.length; i++) {
    desks[i].wallpaperPlugin = "org.kde.image";
    desks[i].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desks[i].writeConfig("Image", "file:///usr/share/wallpapers/NounoursOS/");
    // Widgets NounoursOS : horloge et moniteur, en haut à droite
    var geo = screenGeometry(desks[i].screen);
    var u = gridUnit;
    desks[i].addWidget("org.nounoursos.horloge", geo.width - 25 * u, 4 * u, 22 * u, 10 * u);
    desks[i].addWidget("org.nounoursos.moniteur", geo.width - 21 * u, (4 + 11) * u, 18 * u, 11 * u);
}

// --- Barre du haut ------------------------------------------------------------
var top = new Panel;
top.location = "top";
top.height = Math.round(gridUnit * 1.6);
try { top.floating = false; } catch (e) {}

var menu = top.addWidget("org.kde.plasma.kickoff");
menu.currentConfigGroup = ["General"];
menu.writeConfig("icon", "nounoursos");

top.addWidget("org.kde.plasma.appmenu");
top.addWidget("org.kde.plasma.panelspacer");
top.addWidget("org.nounoursos.controle");   // Centre de contrôle NounoursOS
top.addWidget("org.kde.plasma.systemtray");

var clock = top.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", true);
clock.writeConfig("dateDisplayFormat", "BesideTime");

// --- Dock du bas ---------------------------------------------------------------
var dock = new Panel;
dock.location = "bottom";
dock.height = Math.round(gridUnit * 3.2);
try { dock.alignment = "center"; } catch (e) {}
try { dock.lengthMode = "fit"; } catch (e) {}      // Plasma ≥ 6.1
try { dock.floating = true; } catch (e) {}
try { dock.hiding = "dodgewindows"; } catch (e) {}

var tasks = dock.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:org.kde.dolphin.desktop",
    "preferred://browser",
    "applications:NounoursLauncher.desktop",
    "applications:org.kde.konsole.desktop",
    "applications:org.kde.kate.desktop",
    "applications:org.kde.discover.desktop",
    "applications:nounoursos-parametres.desktop"
]);
tasks.writeConfig("iconSpacing", 2);

dock.addWidget("org.kde.plasma.marginsseparator");
dock.addWidget("org.kde.plasma.trash");
