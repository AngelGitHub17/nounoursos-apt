/* NounoursOS — diaporama affiché pendant l'installation */
import QtQuick 2.0   // fonctionne avec Calamares Qt5 et Qt6
import calamares.slideshow 1.0

Presentation {
    id: presentation

    function nextSlide() {
        presentation.goToNextSlide();
    }

    Timer {
        id: advanceTimer
        interval: 6000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: nextSlide()
    }

    Slide {
        Image {
            source: "slide1.png"
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
        }
    }

    Slide {
        Image {
            source: "slide2.png"
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
        }
    }

    Slide {
        Image {
            source: "slide3.png"
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
        }
    }

    function onActivate()  { presentation.currentSlide = 0; }
    function onLeave()     { }
}
