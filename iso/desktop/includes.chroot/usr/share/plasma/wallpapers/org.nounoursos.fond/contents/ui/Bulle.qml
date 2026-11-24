// Tache de lumière douce (dégradé radial), peinte une fois puis déplacée par le GPU
import QtQuick

Canvas {
    id: c
    property color couleur: "white"
    renderStrategy: Canvas.Cooperative
    onCouleurChanged: requestPaint()
    onWidthChanged: requestPaint()
    onPaint: {
        var ctx = getContext("2d");
        ctx.reset();
        var r = width / 2;
        var g = ctx.createRadialGradient(r, r, 0, r, r, r);
        g.addColorStop(0, Qt.rgba(couleur.r, couleur.g, couleur.b, 1));
        g.addColorStop(0.45, Qt.rgba(couleur.r, couleur.g, couleur.b, 0.45));
        g.addColorStop(1, Qt.rgba(couleur.r, couleur.g, couleur.b, 0));
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, width, height);
    }
}
