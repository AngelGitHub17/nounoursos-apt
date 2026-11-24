// Écran de chargement de la session NounoursOS (ksplash)
import QtQuick

Rectangle {
    id: racine
    color: "#1B1329"
    property int stage: 0

    Image {
        anchors.fill: parent
        source: "file:///usr/share/nounoursos/grub-background.png"
        fillMode: Image.PreserveAspectCrop
        opacity: 0.55
    }

    Column {
        anchors.centerIn: parent
        spacing: 22
        Image {
            id: logo
            anchors.horizontalCenter: parent.horizontalCenter
            source: "file:///usr/share/nounoursos/logo.svg"
            sourceSize: Qt.size(150, 150)
            width: 150; height: 150
            opacity: 0
            scale: 0.9
            NumberAnimation on opacity { to: 1; duration: 500; easing.type: Easing.OutCubic }
            NumberAnimation on scale { to: 1; duration: 700; easing.type: Easing.OutBack }
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            textFormat: Text.StyledText
            text: "Nounours<font color='#F5B862'><b>OS</b></font>"
            color: "white"
            font { family: "Inter Display"; pixelSize: 44; weight: Font.Bold }
        }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 220; height: 5; radius: 3
            color: Qt.rgba(1, 1, 1, 0.15)
            Rectangle {
                height: parent.height; radius: 3
                width: parent.width * Math.min(1, racine.stage / 6)
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: "#F5B862" }
                    GradientStop { position: 1; color: "#D98A3F" }
                }
                Behavior on width { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
            }
        }
    }
    Text {
        anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 36 }
        text: "Doux dehors, solide dedans."
        color: "#CDB8DA"
        font { family: "Inter"; pixelSize: 15 }
    }
}
