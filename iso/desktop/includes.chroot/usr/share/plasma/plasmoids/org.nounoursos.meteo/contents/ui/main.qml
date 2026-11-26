// Météo NounoursOS : Open-Meteo (gratuit, sans clé ni compte).
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation
    property var actuel: null
    property var jours: []
    property string message: "Chargement…"

    function charger() {
        var c = Plasmoid.configuration;
        var url = "https://api.open-meteo.com/v1/forecast?latitude=" + c.Latitude + "&longitude=" + c.Longitude +
                  "&current=temperature_2m,apparent_temperature,weather_code,is_day,wind_speed_10m" +
                  "&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=5";
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== XMLHttpRequest.DONE) return;
            try {
                var d = JSON.parse(xhr.responseText);
                root.actuel = { temperature: d.current.temperature_2m, ressenti: d.current.apparent_temperature,
                                code: d.current.weather_code, jour: d.current.is_day === 1, vent: d.current.wind_speed_10m };
                var j = [];
                for (var i = 0; i < d.daily.time.length; i++)
                    j.push({ date: new Date(d.daily.time[i] + "T12:00:00"), code: d.daily.weather_code[i],
                             max: d.daily.temperature_2m_max[i], min: d.daily.temperature_2m_min[i] });
                root.jours = j;
                root.message = "";
            } catch (e) {
                if (!root.actuel) root.message = "Météo indisponible pour le moment.";
            }
        };
        xhr.open("GET", url);
        xhr.send();
    }
    Connections {
        target: Plasmoid.configuration
        function onLatitudeChanged() { root.charger() }
        function onLongitudeChanged() { root.charger() }
    }
    Timer { interval: 20 * 60 * 1000; repeat: true; running: true; triggeredOnStart: true; onTriggered: root.charger() }

    fullRepresentation: Meteo {
        accent: Kirigami.Theme.highlightColor
        ville: Plasmoid.configuration.Ville
        actuel: root.actuel
        jours: root.jours
        message: root.message
        Layout.preferredWidth: Kirigami.Units.gridUnit * 18
        Layout.preferredHeight: Kirigami.Units.gridUnit * 12
        Layout.minimumWidth: Kirigami.Units.gridUnit * 13
        Layout.minimumHeight: Kirigami.Units.gridUnit * 9
    }
}
