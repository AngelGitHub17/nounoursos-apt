// Partie visible du moniteur (sans dépendance Plasma : testable seule).
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: m
    property color accent: "#C9864B"
    property real cpu: 0
    property real ram: 0
    property string ramTexte: ""
    property real disque: 0
    property real temperature: 0
    property string descente: "—"
    property string montee: "—"

    radius: 18
    color: Qt.rgba(0.08, 0.06, 0.12, 0.55)
    border.color: Qt.rgba(1, 1, 1, 0.12)

    component Ligne: ColumnLayout {
        property string nom
        property string valeur
        property real fraction: 0
        property bool alerte: false
        spacing: 4
        Layout.fillWidth: true
        RowLayout {
            Layout.fillWidth: true
            Text { text: nom; color: "#F6ECDE"; opacity: 0.75; font.pixelSize: 12; font.family: "Noto Sans" }
            Item { Layout.fillWidth: true }
            Text { text: valeur; color: "#F6ECDE"; font.pixelSize: 12; font.family: "Noto Sans"; font.bold: true }
        }
        Rectangle {
            Layout.fillWidth: true
            height: 6; radius: 3
            color: Qt.rgba(1, 1, 1, 0.14)
            Rectangle {
                height: parent.height; radius: 3
                width: Math.max(6, parent.width * Math.min(1, Math.max(0, fraction)))
                color: alerte ? "#FF6B6B" : m.accent
                Behavior on width { NumberAnimation { duration: 500; easing.type: Easing.OutCubic } }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 10
        Text {
            text: "RESSOURCES"
            color: m.accent
            font.pixelSize: 11; font.bold: true; font.letterSpacing: 2; font.family: "Noto Sans"
        }
        Ligne { nom: "Processeur"; valeur: Math.round(m.cpu) + " %"; fraction: m.cpu / 100 }
        Ligne { nom: "Mémoire"; valeur: m.ramTexte || (Math.round(m.ram) + " %"); fraction: m.ram / 100 }
        Ligne { nom: "Disque"; valeur: Math.round(m.disque) + " %"; fraction: m.disque / 100 }
        Ligne {
            visible: m.temperature > 0
            nom: "Température"; valeur: Math.round(m.temperature) + " °C"
            fraction: m.temperature / 100; alerte: m.temperature >= 88
        }
        Text {
            text: "↓ " + m.descente + "    ↑ " + m.montee
            color: "#F6ECDE"; opacity: 0.75; font.pixelSize: 12; font.family: "Noto Sans"
        }
        Item { Layout.fillHeight: true }
    }
}
