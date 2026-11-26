// Agenda NounoursOS : prochains rendez-vous depuis des liens ICS.
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami
import "ics.js" as ICS

PlasmoidItem {
    id: root
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation
    property var evenements: []
    property string message: ""
    property var textes: ({})
    property date maintenant: new Date()

    function charger() {
        var liens = Plasmoid.configuration.Liens.split(/\s+/).filter(function (l) { return l.length > 8; });
        if (!liens.length) {
            message = "Ajoutez votre agenda (iCloud, Google, Nextcloud…) : clic droit › Configurer l'agenda.";
            evenements = [];
            return;
        }
        textes = ({});
        var restants = liens.length;
        liens.forEach(function (lien) {
            var url = lien.replace(/^webcals?:\/\//, "https://");
            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function () {
                if (xhr.readyState !== XMLHttpRequest.DONE) return;
                if (xhr.status === 200) textes[url] = xhr.responseText;
                if (--restants === 0) assembler(liens.length);
            };
            xhr.open("GET", url);
            xhr.send();
        });
    }
    function assembler(nb) {
        var tous = [], lus = 0;
        for (var u in textes) {
            lus++;
            tous = tous.concat(ICS.aVenir(textes[u], new Date(), Plasmoid.configuration.Jours, 40));
        }
        tous.sort(function (a, b) { return a.debut - b.debut; });
        evenements = tous.slice(0, 12);
        message = lus === 0 ? "Agenda injoignable pour le moment." :
                  (evenements.length ? "" : "Rien de prévu les " + Plasmoid.configuration.Jours + " prochains jours.");
    }

    Connections {
        target: Plasmoid.configuration
        function onLiensChanged() { root.charger() }
        function onJoursChanged() { root.charger() }
    }
    Timer { interval: 15 * 60 * 1000; repeat: true; running: true; triggeredOnStart: true; onTriggered: root.charger() }
    Timer { interval: 60 * 1000; repeat: true; running: true; onTriggered: root.maintenant = new Date() }

    fullRepresentation: Agenda {
        maintenant: root.maintenant
        accent: Kirigami.Theme.highlightColor
        evenements: root.evenements
        message: root.message
        Layout.preferredWidth: Kirigami.Units.gridUnit * 18
        Layout.preferredHeight: Kirigami.Units.gridUnit * 15
        Layout.minimumWidth: Kirigami.Units.gridUnit * 12
        Layout.minimumHeight: Kirigami.Units.gridUnit * 8
    }
}
