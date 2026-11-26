// Centre de contrôle NounoursOS : contenu du panneau (autonome, testable sans Plasma).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2

Item {
    id: cc
    property var etat: ({})
    property color accent: "#D98A3F"
    property color texte: "#2A1B3D"
    property color fond: "#F4EFEA"
    readonly property color carte: Qt.rgba(texte.r, texte.g, texte.b, 0.07)
    signal commande(string args)

    implicitWidth: 380
    implicitHeight: colonne.implicitHeight + 24

    component Tuile: Rectangle {
        id: t
        property string titre
        property string sousTitre
        property string glyphe
        property bool actif: false
        property bool disponible: true
        signal bascule()
        visible: disponible
        Layout.fillWidth: true
        Layout.preferredHeight: 64
        radius: 18
        color: actif ? cc.accent : cc.carte
        Behavior on color { ColorAnimation { duration: 160 } }
        RowLayout {
            anchors { fill: parent; leftMargin: 12; rightMargin: 10 }
            spacing: 10
            Rectangle {
                Layout.preferredWidth: 32; Layout.preferredHeight: 32; radius: 16
                color: t.actif ? Qt.rgba(1, 1, 1, 0.25) : Qt.rgba(cc.texte.r, cc.texte.g, cc.texte.b, 0.10)
                Text { anchors.centerIn: parent; text: t.glyphe; font.pixelSize: 17
                       color: t.actif ? "white" : cc.texte }
            }
            ColumnLayout {
                spacing: 0
                Layout.fillWidth: true
                Text { text: t.titre; font.pixelSize: 13; font.weight: Font.DemiBold
                       color: t.actif ? "white" : cc.texte; elide: Text.ElideRight; Layout.fillWidth: true }
                Text { text: t.sousTitre; visible: text !== ""; font.pixelSize: 11; elide: Text.ElideRight
                       Layout.fillWidth: true
                       color: t.actif ? Qt.rgba(1, 1, 1, 0.85) : Qt.rgba(cc.texte.r, cc.texte.g, cc.texte.b, 0.6) }
            }
        }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: t.bascule() }
    }

    component Glissiere: RowLayout {
        id: g
        property string glyphe
        property string titre
        property int valeur: 0
        signal change(int v)
        spacing: 10
        Text { text: g.glyphe; font.pixelSize: 16; color: cc.texte; Layout.preferredWidth: 22 }
        ColumnLayout {
            spacing: 0
            Layout.fillWidth: true
            Text { text: g.titre; font.pixelSize: 12; font.weight: Font.DemiBold; color: cc.texte }
            QQC2.Slider {
                id: s
                Layout.fillWidth: true
                from: 0; to: 100; stepSize: 1
                value: g.valeur
                onMoved: minuteur.restart()
                Timer { id: minuteur; interval: 120; onTriggered: g.change(Math.round(s.value)) }
            }
        }
        Text { text: Math.round(s.value) + " %"; font.pixelSize: 11; Layout.preferredWidth: 38
               color: Qt.rgba(cc.texte.r, cc.texte.g, cc.texte.b, 0.6) }
    }

    ColumnLayout {
        id: colonne
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
        spacing: 10

        GridLayout {
            columns: 2
            columnSpacing: 8; rowSpacing: 8
            Layout.fillWidth: true
            Tuile {
                titre: "Wi-Fi"; glyphe: "📶"
                disponible: cc.etat.wifi !== null && cc.etat.wifi !== undefined
                actif: !!cc.etat.wifi
                sousTitre: cc.etat.wifi ? (cc.etat.ssid || "Non connecté") : "Désactivé"
                onBascule: cc.commande("wifi " + (actif ? "off" : "on"))
            }
            Tuile {
                titre: "Bluetooth"; glyphe: "ᛒ"
                disponible: cc.etat.bluetooth !== null && cc.etat.bluetooth !== undefined
                actif: !!cc.etat.bluetooth
                sousTitre: actif ? "Activé" : "Désactivé"
                onBascule: cc.commande("bluetooth " + (actif ? "off" : "on"))
            }
            Tuile {
                titre: "Ne pas déranger"; glyphe: "🌙"
                actif: !!cc.etat.ndp
                sousTitre: cc.etat.mode ? "Via le mode" : (actif ? "Notifications coupées" : "")
                onBascule: cc.commande("ndp " + (cc.etat.ndp_seul ? "off" : "on"))
            }
            Tuile {
                titre: "Mode sombre"; glyphe: "◐"
                actif: !!cc.etat.sombre
                sousTitre: actif ? "Activé" : "Désactivé"
                onBascule: cc.commande("sombre " + (actif ? "off" : "on"))
            }
        }

        // Modes Concentration
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: modes.implicitHeight + 20
            radius: 18
            color: cc.carte
            ColumnLayout {
                id: modes
                anchors { fill: parent; margins: 10 }
                spacing: 8
                Text { text: "Concentration"; font.pixelSize: 12; font.weight: Font.DemiBold; color: cc.texte }
                RowLayout {
                    spacing: 6
                    Layout.fillWidth: true
                    Repeater {
                        model: cc.etat.modes || []
                        delegate: Rectangle {
                            required property var modelData
                            readonly property bool actif: cc.etat.mode === modelData[0]
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            radius: 12
                            color: actif ? cc.accent : Qt.rgba(cc.texte.r, cc.texte.g, cc.texte.b, 0.08)
                            Text {
                                anchors.centerIn: parent
                                text: modelData[2] + " " + modelData[1]
                                font.pixelSize: 12; font.weight: actif ? Font.DemiBold : Font.Normal
                                color: actif ? "white" : cc.texte
                            }
                            MouseArea {
                                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                onClicked: cc.commande("mode " + (parent.actif ? "aucun" : modelData[0]))
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: glissieres.implicitHeight + 20
            radius: 18
            color: cc.carte
            visible: cc.etat.volume !== null || cc.etat.luminosite !== null
            ColumnLayout {
                id: glissieres
                anchors { fill: parent; margins: 10 }
                spacing: 4
                Glissiere {
                    Layout.fillWidth: true
                    visible: cc.etat.volume !== null && cc.etat.volume !== undefined
                    glyphe: cc.etat.muet ? "🔇" : "🔊"; titre: "Son"
                    valeur: cc.etat.volume || 0
                    onChange: (v) => cc.commande("volume " + v)
                }
                Glissiere {
                    Layout.fillWidth: true
                    visible: cc.etat.luminosite !== null && cc.etat.luminosite !== undefined
                    glyphe: "☀"; titre: "Luminosité"
                    valeur: cc.etat.luminosite || 0
                    onChange: (v) => cc.commande("luminosite " + v)
                }
            }
        }

        RowLayout {
            spacing: 8
            Layout.fillWidth: true
            Tuile {
                titre: "Capture"; glyphe: "⌗"; Layout.preferredHeight: 46
                onBascule: cc.commande("capture")
            }
            Tuile {
                titre: "Paramètres"; glyphe: "⚙"; Layout.preferredHeight: 46
                onBascule: cc.commande("parametres")
            }
        }
    }
}
