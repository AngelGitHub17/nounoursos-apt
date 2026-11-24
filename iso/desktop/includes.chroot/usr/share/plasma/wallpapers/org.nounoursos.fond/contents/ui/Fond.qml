// Fond animé NounoursOS — composant autonome (testable avec « qml Fond.qml »)
import QtQuick

Rectangle {
    id: fond
    width: 1280; height: 720
    property string teinte: "Miel"
    property real vitesse: 1.0           // 0 = figé
    property bool actif: true            // false quand une fenêtre couvre l'écran

    readonly property var teintes: ({
        "Miel":      ["#C9864B", "#F3B562"],
        "Myrtille":  ["#3D7EDB", "#8DB8F5"],
        "Lavande":   ["#7E57C2", "#C2A8F0"],
        "Menthe":    ["#3FA36B", "#8FE0B2"],
        "Framboise": ["#D9568C", "#F5A3C4"],
        "Graphite":  ["#6B6478", "#C9C2D4"]
    })
    property color accent: (teintes[teinte] || teintes["Miel"])[0]
    property color lueur: (teintes[teinte] || teintes["Miel"])[1]
    readonly property bool anime: actif && vitesse > 0
    property real t: 0

    // 25 images/s suffisent pour un mouvement aussi lent, et ménagent le processeur
    Timer {
        interval: 40; repeat: true; running: fond.anime
        onTriggered: fond.t += 0.4 * fond.vitesse
    }

    gradient: Gradient {
        orientation: Gradient.Vertical
        GradientStop { position: 0; color: "#1F1A2E" }
        GradientStop { position: 0.6; color: "#33264A" }
        GradientStop { position: 1; color: Qt.darker(fond.accent, 2.2) }
    }

    // Grandes bulles de lumière qui dérivent lentement
    Repeater {
        model: 5
        Bulle {
            readonly property real phase: index * 1.7
            readonly property real taille: fond.height * (0.7 + 0.2 * (index % 3))
            width: taille; height: taille
            couleur: index % 2 ? fond.lueur : fond.accent
            x: fond.width * (0.1 + 0.8 * (0.5 + 0.5 * Math.sin(fond.t * 0.011 + phase))) - taille / 2
            y: fond.height * (0.3 + 0.6 * (0.5 + 0.5 * Math.cos(fond.t * 0.008 + phase * 1.3))) - taille / 2
            opacity: 0.22
        }
    }

    // Lueur principale en bas à droite
    Bulle {
        width: fond.width * 1.3; height: width
        x: fond.width * 0.75 - width / 2; y: fond.height * 0.95 - height / 2
        couleur: fond.lueur
        opacity: 0.32 + 0.08 * Math.sin(fond.t * 0.05)
    }

    // Petites particules qui montent
    Repeater {
        model: 28
        Rectangle {
            readonly property real graine: (index * 7919) % 1000 / 1000
            readonly property real vy: 0.4 + graine * 0.9
            width: 3 + graine * 5; height: width; radius: width / 2
            color: graine > 0.5 ? fond.lueur : "#FFFFFF"
            x: fond.width * ((graine * 13.37) % 1) + 30 * Math.sin(fond.t * 0.03 + index)
            y: fond.height - ((fond.t * vy * 2.5 + graine * fond.height) % (fond.height + 40))
            opacity: 0.12 + 0.25 * graine
        }
    }

    // Ourson (silhouette) qui respire
    Item {
        id: ourson
        width: fond.height * 0.42; height: width * 0.86
        x: fond.width * 0.68 - width / 2; y: fond.height * 0.42 - height / 2
        scale: 1 + 0.015 * Math.sin(fond.t * 0.12)
        opacity: 0.07
        Rectangle { width: parent.width * 0.3; height: width; radius: width / 2; color: "white"; x: 0; y: 0 }
        Rectangle { width: parent.width * 0.3; height: width; radius: width / 2; color: "white"; x: parent.width * 0.7; y: 0 }
        Rectangle { width: parent.width * 0.74; height: parent.height * 0.8; radius: width / 2; color: "white"
                    x: parent.width * 0.13; y: parent.height * 0.2 }
    }

    Behavior on accent { ColorAnimation { duration: 800 } }
    Behavior on lueur { ColorAnimation { duration: 800 } }
}
