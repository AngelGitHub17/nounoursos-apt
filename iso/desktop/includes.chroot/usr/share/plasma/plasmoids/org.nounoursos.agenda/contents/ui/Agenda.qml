// Agenda NounoursOS : carte translucide (autonome, testable sans Plasma).
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: ag
    property color accent: "#D98A3F"
    property var evenements: []        // [{titre, lieu, debut: Date, fin: Date, journee}]
    property string message: ""
    property date maintenant: new Date()
    implicitWidth: 340
    implicitHeight: 300
    radius: 22
    color: Qt.rgba(0.106, 0.075, 0.161, 0.55)
    border.color: Qt.rgba(1, 1, 1, 0.12)

    function jourDe(d) {
        var a = new Date(maintenant.getFullYear(), maintenant.getMonth(), maintenant.getDate());
        var b = new Date(d.getFullYear(), d.getMonth(), d.getDate());
        var n = Math.round((b - a) / 86400000);
        if (n <= 0) return "Aujourd'hui";
        if (n === 1) return "Demain";
        var t = Qt.locale("fr_FR").toString(d, "dddd d MMMM");
        return t.charAt(0).toUpperCase() + t.slice(1);
    }

    ColumnLayout {
        anchors { fill: parent; margins: 16 }
        spacing: 8
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                spacing: -2
                Text { text: "AGENDA"; color: ag.accent; font.pixelSize: 12; font.weight: Font.Bold; font.letterSpacing: 1.5 }
                Text {
                    text: { var t = Qt.locale("fr_FR").toString(ag.maintenant, "dddd d MMMM"); return t.charAt(0).toUpperCase() + t.slice(1) }
                    color: "white"; font.pixelSize: 19; font.weight: Font.DemiBold
                }
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                Layout.preferredWidth: 44; Layout.preferredHeight: 48; radius: 10; color: "white"
                Rectangle { width: parent.width; height: 14; radius: 10; color: ag.accent
                            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 6; color: ag.accent } }
                Text { anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 4 }
                       text: ag.maintenant.getDate(); color: "#2A1B3D"; font.pixelSize: 22; font.weight: Font.Bold }
            }
        }
        Text {
            visible: ag.message !== ""
            Layout.fillWidth: true
            text: ag.message
            wrapMode: Text.WordWrap
            color: Qt.rgba(1, 1, 1, 0.75); font.pixelSize: 13
        }
        ListView {
            id: liste
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 6
            model: ag.evenements
            section.property: "jour"
            delegate: RowLayout {
                required property var modelData
                required property int index
                width: liste.width
                spacing: 10
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        visible: index === 0 || ag.jourDe(ag.evenements[index - 1].debut) !== ag.jourDe(modelData.debut)
                        text: ag.jourDe(modelData.debut)
                        color: ag.accent; font.pixelSize: 12; font.weight: Font.DemiBold
                        topPadding: index === 0 ? 0 : 6
                    }
                    RowLayout {
                        spacing: 10
                        Rectangle { Layout.preferredWidth: 4; Layout.fillHeight: true; radius: 2; color: ag.accent; opacity: 0.9 }
                        ColumnLayout {
                            spacing: 0
                            Layout.fillWidth: true
                            Text { text: modelData.titre; color: "white"; font.pixelSize: 14; font.weight: Font.Medium
                                   elide: Text.ElideRight; Layout.fillWidth: true }
                            Text {
                                text: (modelData.journee ? "Toute la journée" :
                                       Qt.formatTime(modelData.debut, "HH:mm") + " – " + Qt.formatTime(modelData.fin, "HH:mm"))
                                      + (modelData.lieu ? " · " + modelData.lieu : "")
                                color: Qt.rgba(1, 1, 1, 0.7); font.pixelSize: 12; elide: Text.ElideRight; Layout.fillWidth: true
                            }
                        }
                    }
                }
            }
        }
    }
}
