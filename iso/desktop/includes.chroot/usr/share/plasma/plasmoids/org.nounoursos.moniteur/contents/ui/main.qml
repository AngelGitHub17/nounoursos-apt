// Moniteur NounoursOS : ressources de la machine (capteurs KDE ksystemstats).
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami
import org.kde.ksysguard.sensors as Sensors

PlasmoidItem {
    id: root
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation

    Sensors.Sensor { id: cpu;    sensorId: "cpu/all/usage";               updateRateLimit: 2000 }
    Sensors.Sensor { id: ram;    sensorId: "memory/physical/usedPercent"; updateRateLimit: 2000 }
    Sensors.Sensor { id: ramUsed; sensorId: "memory/physical/used";       updateRateLimit: 4000 }
    Sensors.Sensor { id: ramTot; sensorId: "memory/physical/total";       updateRateLimit: 60000 }
    Sensors.Sensor { id: disk;   sensorId: "disk/all/usedPercent";        updateRateLimit: 10000 }
    Sensors.Sensor { id: temp;   sensorId: "cpu/all/maximumTemperature";  updateRateLimit: 2000 }
    Sensors.Sensor { id: down;   sensorId: "network/all/download";        updateRateLimit: 2000 }
    Sensors.Sensor { id: up;     sensorId: "network/all/upload";          updateRateLimit: 2000 }

    fullRepresentation: Moniteur {
        accent: Kirigami.Theme.highlightColor
        Layout.preferredWidth: Kirigami.Units.gridUnit * 18
        Layout.preferredHeight: Kirigami.Units.gridUnit * 11
        Layout.minimumWidth: Kirigami.Units.gridUnit * 12
        Layout.minimumHeight: Kirigami.Units.gridUnit * 9
        cpu: cpu.value || 0
        ram: ram.value || 0
        ramTexte: ramUsed.formattedValue + " / " + ramTot.formattedValue
        disque: disk.value || 0
        temperature: temp.value || 0
        descente: down.formattedValue
        montee: up.formattedValue
    }
}
