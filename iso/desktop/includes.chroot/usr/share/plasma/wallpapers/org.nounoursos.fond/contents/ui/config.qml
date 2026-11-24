import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    id: page
    property string cfg_Teinte
    property int cfg_Vitesse

    QQC2.ComboBox {
        Kirigami.FormData.label: "Teinte :"
        model: ["Miel", "Myrtille", "Lavande", "Menthe", "Framboise", "Graphite"]
        currentIndex: Math.max(0, model.indexOf(page.cfg_Teinte))
        onActivated: page.cfg_Teinte = currentText
    }
    QQC2.Slider {
        Kirigami.FormData.label: "Vitesse :"
        from: 0; to: 300; stepSize: 25
        value: page.cfg_Vitesse
        onMoved: page.cfg_Vitesse = value
    }
}
