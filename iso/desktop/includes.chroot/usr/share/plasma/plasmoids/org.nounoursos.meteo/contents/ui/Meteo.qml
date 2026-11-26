// Météo NounoursOS : carte translucide (autonome, testable sans Plasma).
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: mt
    property color accent: "#D98A3F"
    property string ville: ""
    property var actuel: null          // {temperature, ressenti, code, jour, vent}
    property var jours: []             // [{date: Date, code, max, min}]
    property string message: ""
    implicitWidth: 340
    implicitHeight: 220
    radius: 22
    color: Qt.rgba(0.106, 0.075, 0.161, 0.55)
    border.color: Qt.rgba(1, 1, 1, 0.12)

    // Codes météo WMO → description et symbole
    function info(code, jour) {
        var c = code
        if (c === 0) return [jour === false ? "🌙" : "☀️", "Ciel dégagé"]
        if (c === 1) return [jour === false ? "🌙" : "🌤️", "Plutôt dégagé"]
        if (c === 2) return ["⛅", "Partiellement nuageux"]
        if (c === 3) return ["☁️", "Couvert"]
        if (c === 45 || c === 48) return ["🌫️", "Brouillard"]
        if (c >= 51 && c <= 57) return ["🌦️", "Bruine"]
        if (c >= 61 && c <= 67) return ["🌧️", c >= 66 ? "Pluie verglaçante" : "Pluie"]
        if (c >= 71 && c <= 77) return ["🌨️", "Neige"]
        if (c >= 80 && c <= 82) return ["🌦️", "Averses"]
        if (c === 85 || c === 86) return ["🌨️", "Averses de neige"]
        if (c >= 95) return ["⛈️", "Orage"]
        return ["🌡️", ""]
    }

    ColumnLayout {
        anchors { fill: parent; margins: 16 }
        spacing: 6
        Text { text: "MÉTÉO · " + mt.ville.toUpperCase(); color: mt.accent; font.pixelSize: 12
               font.weight: Font.Bold; font.letterSpacing: 1.5; elide: Text.ElideRight; Layout.fillWidth: true }
        Text { visible: mt.message !== ""; text: mt.message; color: Qt.rgba(1, 1, 1, 0.75); font.pixelSize: 13
               wrapMode: Text.WordWrap; Layout.fillWidth: true }
        RowLayout {
            visible: mt.actuel !== null
            spacing: 14
            Text { text: mt.actuel ? mt.info(mt.actuel.code, mt.actuel.jour)[0] : ""; font.pixelSize: 54 }
            ColumnLayout {
                spacing: -4
                Text { text: mt.actuel ? Math.round(mt.actuel.temperature) + "°" : ""; color: "white"
                       font.pixelSize: 52; font.weight: Font.Light }
                Text { text: mt.actuel ? mt.info(mt.actuel.code, mt.actuel.jour)[1] : ""; color: "white"; font.pixelSize: 14 }
                Text { text: mt.actuel ? "Ressenti " + Math.round(mt.actuel.ressenti) + "° · vent " + Math.round(mt.actuel.vent) + " km/h" : ""
                       color: Qt.rgba(1, 1, 1, 0.7); font.pixelSize: 12; topPadding: 4 }
            }
        }
        Item { Layout.fillHeight: true }
        RowLayout {
            Layout.fillWidth: true
            spacing: 4
            Repeater {
                model: mt.jours
                delegate: ColumnLayout {
                    required property var modelData
                    required property int index
                    Layout.fillWidth: true
                    spacing: 0
                    Text { Layout.alignment: Qt.AlignHCenter; color: Qt.rgba(1, 1, 1, 0.8); font.pixelSize: 12
                           text: index === 0 ? "Auj." : Qt.locale("fr_FR").toString(modelData.date, "ddd").replace(".", "") }
                    Text { Layout.alignment: Qt.AlignHCenter; font.pixelSize: 20; text: mt.info(modelData.code, true)[0] }
                    Text { Layout.alignment: Qt.AlignHCenter; color: "white"; font.pixelSize: 12
                           text: Math.round(modelData.max) + "° <font color='#B8A9C9'>" + Math.round(modelData.min) + "°</font>"
                           textFormat: Text.StyledText }
                }
            }
        }
    }
}
