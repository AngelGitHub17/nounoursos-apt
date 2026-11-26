import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    id: page
    property string cfg_Ville
    property real cfg_Latitude
    property real cfg_Longitude

    RowLayout {
        Kirigami.FormData.label: "Ville :"
        QQC2.TextField { id: champ; text: page.cfg_Ville; Layout.preferredWidth: Kirigami.Units.gridUnit * 14
                         onAccepted: chercher() }
        QQC2.Button { text: "Chercher"; onClicked: chercher() }
    }
    QQC2.Label { id: etat; opacity: 0.7; text: page.cfg_Ville ? "Ville actuelle : " + page.cfg_Ville : "" }
    Repeater {
        model: ListModel { id: resultats }
        delegate: QQC2.Button {
            text: nom + (detail ? " — " + detail : "")
            onClicked: { page.cfg_Ville = nom; page.cfg_Latitude = lat; page.cfg_Longitude = lon;
                         etat.text = "Ville choisie : " + nom; resultats.clear() }
        }
    }
    function chercher() {
        resultats.clear();
        etat.text = "Recherche…";
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== XMLHttpRequest.DONE) return;
            try {
                var r = JSON.parse(xhr.responseText).results || [];
                r.forEach(function (v) {
                    resultats.append({ nom: v.name, lat: v.latitude, lon: v.longitude,
                                       detail: [v.admin2 || v.admin1, v.country].filter(Boolean).join(", ") });
                });
                etat.text = r.length ? "Choisissez la bonne ville :" : "Aucune ville trouvée.";
            } catch (e) { etat.text = "Recherche impossible (connexion ?)." }
        };
        xhr.open("GET", "https://geocoding-api.open-meteo.com/v1/search?count=6&language=fr&name=" + encodeURIComponent(champ.text));
        xhr.send();
    }
}
