// Centre de contrôle NounoursOS (barre du haut / tableau de bord).
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root
    property var etat: ({})
    toolTipMainText: "Centre de contrôle"
    toolTipSubText: etat.mode ? "Mode " + etat.mode : (etat.ndp ? "Ne pas déranger" : "")

    P5Support.DataSource {
        id: exe
        engine: "executable"
        connectedSources: []
        onNewData: (source, data) => {
            if (source === "nounoursos-controle etat") {
                try { root.etat = JSON.parse(data["stdout"]) } catch (e) {}
            } else {
                Qt.callLater(root.actualiser)
            }
            disconnectSource(source)
        }
    }
    function actualiser() { exe.connectSource("nounoursos-controle etat") }
    function lancer(args) {
        if (args === "parametres") { exe.connectSource("nounoursos-parametres"); root.expanded = false; return }
        if (args === "capture") root.expanded = false
        exe.connectSource("nounoursos-controle " + args)
    }
    Timer { interval: 3000; repeat: true; running: root.expanded; triggeredOnStart: true; onTriggered: root.actualiser() }
    Component.onCompleted: actualiser()

    compactRepresentation: MouseArea {
        Layout.minimumWidth: Kirigami.Units.iconSizes.smallMedium
        onClicked: root.expanded = !root.expanded
        // Deux interrupteurs, façon centre de contrôle
        Column {
            anchors.centerIn: parent
            spacing: Math.round(parent.height * 0.12)
            Repeater {
                model: 2
                Rectangle {
                    width: Math.round(Math.min(parent.parent.width, parent.parent.height) * 0.72)
                    height: Math.round(width * 0.42); radius: height / 2
                    color: "transparent"; border.width: Math.max(1.5, height * 0.14)
                    border.color: Kirigami.Theme.textColor
                    Rectangle {
                        width: parent.height * 0.5; height: width; radius: width / 2
                        anchors.verticalCenter: parent.verticalCenter
                        x: index === 0 ? parent.width - width - parent.height * 0.25 : parent.height * 0.25
                        color: index === 0 && (root.etat.ndp || root.etat.mode) ? Kirigami.Theme.highlightColor
                                                                                  : Kirigami.Theme.textColor
                    }
                }
            }
        }
    }

    fullRepresentation: Controle {
        Layout.preferredWidth: Kirigami.Units.gridUnit * 25
        Layout.preferredHeight: implicitHeight
        Layout.minimumWidth: Kirigami.Units.gridUnit * 21
        accent: Kirigami.Theme.highlightColor
        texte: Kirigami.Theme.textColor
        etat: root.etat
        onCommande: (args) => root.lancer(args)
    }
}
