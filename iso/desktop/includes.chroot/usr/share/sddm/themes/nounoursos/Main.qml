// Écran de connexion NounoursOS (SDDM, Qt 6)
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: racine
    width: 1920; height: 1080
    color: "#1B1329"

    readonly property color miel: config.accent || "#D98A3F"
    readonly property color mielClair: "#F5B862"
    readonly property color texte: "#FFFFFF"
    readonly property color doux: "#D9CCE4"
    property int session: sessionModel.lastIndex >= 0 ? sessionModel.lastIndex : 0
    property bool echec: false

    Connections {
        target: sddm
        function onLoginFailed() {
            racine.echec = true
            motDePasse.text = ""
            motDePasse.forceActiveFocus()
            secousse.start()
        }
        function onLoginSucceeded() { racine.echec = false }
    }

    Image {
        anchors.fill: parent
        source: config.background || "fond.png"
        fillMode: Image.PreserveAspectCrop
        asynchronous: false
    }
    Rectangle { anchors.fill: parent; color: "#1B1329"; opacity: 0.25 }

    // Heure et date, en haut à gauche
    Column {
        anchors { left: parent.left; top: parent.top; leftMargin: racine.width * 0.05; topMargin: racine.height * 0.07 }
        spacing: 2
        Text {
            id: heure
            color: racine.texte
            font { family: "Inter Display"; pixelSize: racine.height * 0.11; weight: Font.Light }
            text: Qt.formatTime(new Date(), "HH:mm")
        }
        Text {
            id: date
            color: racine.doux
            font { family: "Inter"; pixelSize: racine.height * 0.026; weight: Font.Medium }
            text: { var t = Qt.locale("fr_FR").toString(new Date(), "dddd d MMMM"); return t.charAt(0).toUpperCase() + t.slice(1) }
        }
        Timer {
            interval: 1000; repeat: true; running: true
            onTriggered: {
                heure.text = Qt.formatTime(new Date(), "HH:mm")
                var t = Qt.locale("fr_FR").toString(new Date(), "dddd d MMMM")
                date.text = t.charAt(0).toUpperCase() + t.slice(1)
            }
        }
    }

    // Carte de connexion
    Rectangle {
        id: carte
        width: Math.min(440, racine.width * 0.8); height: colonne.implicitHeight + 64
        anchors.centerIn: parent
        anchors.verticalCenterOffset: racine.height * 0.04
        radius: 28
        color: Qt.rgba(0.106, 0.075, 0.161, 0.62)
        border.color: Qt.rgba(1, 1, 1, 0.12)

        SequentialAnimation {
            id: secousse
            NumberAnimation { target: carte; property: "anchors.horizontalCenterOffset"; to: -14; duration: 50 }
            NumberAnimation { target: carte; property: "anchors.horizontalCenterOffset"; to: 14; duration: 70 }
            NumberAnimation { target: carte; property: "anchors.horizontalCenterOffset"; to: -8; duration: 60 }
            NumberAnimation { target: carte; property: "anchors.horizontalCenterOffset"; to: 0; duration: 50 }
        }

        ColumnLayout {
            id: colonne
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 32 }
            spacing: 14

            Image {
                Layout.alignment: Qt.AlignHCenter
                source: "logo.png"
                sourceSize: Qt.size(104, 104)
                Layout.preferredWidth: 104; Layout.preferredHeight: 104
            }

            // Choix du compte
            ComboBox {
                id: compte
                Layout.fillWidth: true
                Layout.preferredHeight: 46
                model: userModel
                textRole: "realName"
                currentIndex: userModel.lastIndex >= 0 ? userModel.lastIndex : 0
                font { family: "Inter"; pixelSize: 19; weight: Font.DemiBold }
                property string login: ""
                Component.onCompleted: majLogin()
                onCurrentIndexChanged: majLogin()
                function majLogin() {
                    var nom = userModel.data(userModel.index(currentIndex, 0), Qt.UserRole + 1)
                    login = nom ? nom : userModel.lastUser
                }
                displayText: currentText !== "" ? currentText : login
                background: Item {}
                contentItem: Text {
                    text: compte.displayText
                    color: racine.texte
                    font: compte.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                indicator: Item {}
            }

            TextField {
                id: motDePasse
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                echoMode: TextInput.Password
                placeholderText: "Mot de passe"
                placeholderTextColor: "#A898B8"
                color: racine.texte
                font { family: "Inter"; pixelSize: 16 }
                leftPadding: 18; rightPadding: 18
                focus: true
                background: Rectangle {
                    radius: 14
                    color: Qt.rgba(1, 1, 1, 0.08)
                    border.width: motDePasse.activeFocus ? 2 : 1
                    border.color: racine.echec ? "#F07C7C" : (motDePasse.activeFocus ? racine.miel : Qt.rgba(1, 1, 1, 0.18))
                }
                onAccepted: connexion()
                onTextChanged: if (text.length) racine.echec = false
                Keys.onEscapePressed: text = ""
            }

            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                color: racine.echec ? "#F5A3A3" : racine.doux
                font { family: "Inter"; pixelSize: 13 }
                text: racine.echec ? "Mot de passe incorrect, réessayez." :
                      (keyboard.capsLock ? "Majuscules activées" : "Doux dehors, solide dedans.")
            }

            Button {
                id: entrer
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                text: "Se connecter"
                font { family: "Inter"; pixelSize: 16; weight: Font.DemiBold }
                onClicked: connexion()
                contentItem: Text {
                    text: entrer.text; font: entrer.font; color: "#2A1B3D"
                    horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 14
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: entrer.down ? Qt.darker(racine.mielClair, 1.15) : racine.mielClair }
                        GradientStop { position: 1; color: entrer.down ? Qt.darker(racine.miel, 1.15) : racine.miel }
                    }
                }
            }
        }
    }

    function connexion() {
        sddm.login(compte.login, motDePasse.text, racine.session)
    }

    // Session (bas gauche)
    ComboBox {
        id: choixSession
        anchors { left: parent.left; bottom: parent.bottom; margins: 28 }
        width: 260; height: 40
        model: sessionModel
        textRole: "name"
        currentIndex: racine.session
        onActivated: racine.session = currentIndex
        font { family: "Inter"; pixelSize: 14 }
        background: Rectangle { radius: 12; color: Qt.rgba(1, 1, 1, 0.08); border.color: Qt.rgba(1, 1, 1, 0.15) }
        contentItem: Text {
            leftPadding: 14; text: "Session : " + choixSession.displayText; color: racine.doux
            font: choixSession.font; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight
        }
    }

    // Marche / arrêt (bas droite)
    Row {
        anchors { right: parent.right; bottom: parent.bottom; margins: 28 }
        spacing: 10
        Repeater {
            model: [
                { nom: "Veille", ok: sddm.canSuspend, act: function() { sddm.suspend() } },
                { nom: "Redémarrer", ok: sddm.canReboot, act: function() { sddm.reboot() } },
                { nom: "Éteindre", ok: sddm.canPowerOff, act: function() { sddm.powerOff() } }
            ]
            delegate: Button {
                visible: modelData.ok
                text: modelData.nom
                height: 40
                font { family: "Inter"; pixelSize: 14 }
                onClicked: modelData.act()
                contentItem: Text { text: parent.text; font: parent.font; color: racine.doux
                                    horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                background: Rectangle { radius: 12; color: parent.hovered ? Qt.rgba(1, 1, 1, 0.16) : Qt.rgba(1, 1, 1, 0.08)
                                        border.color: Qt.rgba(1, 1, 1, 0.15) }
                leftPadding: 16; rightPadding: 16
            }
        }
    }

    Component.onCompleted: motDePasse.forceActiveFocus()
}
