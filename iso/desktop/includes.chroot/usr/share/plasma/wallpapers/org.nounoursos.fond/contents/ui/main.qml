import QtQuick
import org.kde.plasma.plasmoid

WallpaperItem {
    id: root
    Fond {
        anchors.fill: parent
        teinte: root.configuration.Teinte
        vitesse: root.configuration.Vitesse / 100
    }
}
