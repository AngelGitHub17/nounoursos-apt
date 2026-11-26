import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    property alias cfg_Liens: liens.text
    property alias cfg_Jours: jours.value

    QQC2.TextArea {
        id: liens
        Kirigami.FormData.label: "Liens des agendas (ICS) :"
        Layout.preferredWidth: Kirigami.Units.gridUnit * 24
        Layout.preferredHeight: Kirigami.Units.gridUnit * 5
        placeholderText: "Un lien par ligne : webcal://… ou https://….ics"
        wrapMode: TextEdit.WrapAnywhere
    }
    QQC2.Label {
        Layout.preferredWidth: Kirigami.Units.gridUnit * 24
        wrapMode: Text.WordWrap
        opacity: 0.7
        text: "iPhone / iCloud : app Calendrier › ⓘ à côté de l'agenda › Agenda public › copier le lien.\n" +
              "Google Agenda : Paramètres de l'agenda › Adresse secrète au format iCal."
    }
    QQC2.SpinBox {
        id: jours
        Kirigami.FormData.label: "Afficher les jours à venir :"
        from: 1; to: 31
    }
}
