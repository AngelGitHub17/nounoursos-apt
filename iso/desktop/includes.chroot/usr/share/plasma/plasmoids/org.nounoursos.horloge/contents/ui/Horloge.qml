// Partie visible de l'horloge (sans dépendance Plasma : testable seule).
import QtQuick
import QtQuick.Effects

Item {
    id: horloge
    property color accent: "#F3B562"
    property color texte: "#FFFFFF"
    property date maintenant: new Date()

    Timer {
        interval: 1000; running: true; repeat: true; triggeredOnStart: true
        onTriggered: horloge.maintenant = new Date()
    }

    Item {
        id: contenu
        anchors.fill: parent

        Text {
            id: heure
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            text: Qt.formatTime(horloge.maintenant, "HH:mm")
            color: horloge.texte
            font.pixelSize: Math.min(horloge.height * 0.62, horloge.width * 0.36)
            font.weight: Font.Light
            font.family: "Noto Sans"
        }
        Rectangle {
            id: trait
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: heure.bottom
            anchors.topMargin: -heure.font.pixelSize * 0.08
            width: heure.width * 0.25 * (horloge.maintenant.getSeconds() + 1) / 60 + heure.width * 0.05
            height: Math.max(3, horloge.height * 0.025)
            radius: height / 2
            color: horloge.accent
            Behavior on width { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: trait.bottom
            anchors.topMargin: horloge.height * 0.05
            text: {
                const t = Qt.locale("fr_FR").toString(horloge.maintenant, "dddd d MMMM")
                return t.charAt(0).toUpperCase() + t.slice(1)
            }
            color: horloge.texte
            opacity: 0.85
            font.pixelSize: Math.max(12, horloge.height * 0.13)
            font.family: "Noto Sans"
        }
    }
    MultiEffect {
        source: contenu
        anchors.fill: contenu
        shadowEnabled: true
        shadowColor: "#80000000"
        shadowBlur: 0.6
        shadowVerticalOffset: 2
    }
}
