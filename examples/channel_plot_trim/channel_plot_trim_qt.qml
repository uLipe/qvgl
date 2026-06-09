import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

Item {
    width: 480
    height: 300

    readonly property real xMin: 0
    readonly property real xMax: 5
    readonly property real yMin: -1.1
    readonly property real yMax: 1.3
    readonly property int gridDiv: 4
    readonly property color lineColor: "#4fc3f7"

    readonly property var points: [
        { x: 0.0, y: 0.2 }, { x: 1.0, y: 1.1 }, { x: 2.0, y: -0.3 },
        { x: 3.0, y: -0.5 }, { x: 4.0, y: 1.0 }, { x: 5.0, y: -0.2 }
    ]

    function formatAxis(v) {
        var a = Math.abs(v)
        if (a >= 100)
            return v.toFixed(0)
        if (a >= 10)
            return v.toFixed(1)
        if (a >= 1)
            return v.toFixed(2)
        return v.toFixed(3)
    }

    Rectangle {
        anchors.fill: parent
        color: "#18191c"
        radius: 8

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Rectangle {
                    width: 10
                    height: 10
                    radius: 5
                    color: lineColor
                }

                Label {
                    text: "Phase current Ia"
                    Layout.fillWidth: true
                    color: Material.foreground
                    font.pixelSize: 14
                }

                Label {
                    text: "A"
                    color: lineColor
                    font.pixelSize: 12
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                Canvas {
                    id: plotCanvas
                    anchors.fill: parent

                    readonly property int padL: 52
                    readonly property int padR: 10
                    readonly property int padT: 10
                    readonly property int padB: 30

                    function plotWidth() { return width - padL - padR }
                    function plotHeight() { return height - padT - padB }

                    function mapX(x) {
                        return padL + (x - xMin) / (xMax - xMin) * plotWidth()
                    }

                    function mapY(y) {
                        return padT + (1 - (y - yMin) / (yMax - yMin)) * plotHeight()
                    }

                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()
                        ctx.fillStyle = "#0d0d0f"
                        ctx.fillRect(0, 0, width, height)

                        var w = plotWidth()
                        var h = plotHeight()
                        if (w <= 0 || h <= 0)
                            return

                        ctx.strokeStyle = "#2a2b2f"
                        ctx.lineWidth = 1
                        for (var gx = 0; gx <= gridDiv; gx++) {
                            var xx = padL + gx / gridDiv * w
                            ctx.beginPath()
                            ctx.moveTo(xx, padT)
                            ctx.lineTo(xx, padT + h)
                            ctx.stroke()
                        }
                        for (var gy = 0; gy <= gridDiv; gy++) {
                            var yy = padT + gy / gridDiv * h
                            ctx.beginPath()
                            ctx.moveTo(padL, yy)
                            ctx.lineTo(padL + w, yy)
                            ctx.stroke()
                        }

                        ctx.strokeStyle = "#3d3e42"
                        ctx.lineWidth = 1.5
                        ctx.beginPath()
                        ctx.moveTo(padL, padT + h)
                        ctx.lineTo(padL + w, padT + h)
                        ctx.stroke()
                        ctx.beginPath()
                        ctx.moveTo(padL, padT)
                        ctx.lineTo(padL, padT + h)
                        ctx.stroke()

                        ctx.fillStyle = "#9aa0a6"
                        ctx.font = "10px monospace"
                        ctx.textAlign = "center"
                        ctx.textBaseline = "top"
                        for (gx = 0; gx <= gridDiv; gx++) {
                            var tx = xMin + gx / gridDiv * (xMax - xMin)
                            xx = padL + gx / gridDiv * w
                            ctx.fillText(formatAxis(tx), xx, padT + h + 5)
                        }
                        ctx.textAlign = "right"
                        ctx.textBaseline = "middle"
                        for (gy = 0; gy <= gridDiv; gy++) {
                            var ty = yMax - gy / gridDiv * (yMax - yMin)
                            yy = padT + gy / gridDiv * h
                            ctx.fillText(formatAxis(ty), padL - 6, yy)
                        }
                        ctx.textAlign = "left"
                        ctx.textBaseline = "alphabetic"
                        ctx.font = "9px sans-serif"
                        ctx.fillStyle = "#6b7075"
                        ctx.fillText("t (s)", padL + w - 28, padT + h + 5)
                        ctx.fillText("A", 2, padT + 10)

                        if (points.length >= 2) {
                            ctx.strokeStyle = lineColor
                            ctx.lineWidth = 2
                            ctx.beginPath()
                            ctx.moveTo(mapX(points[0].x), mapY(points[0].y))
                            for (var k = 1; k < points.length; k++)
                                ctx.lineTo(mapX(points[k].x), mapY(points[k].y))
                            ctx.stroke()
                        }
                    }

                    Component.onCompleted: requestPaint()
                }
            }

            Label {
                text: ""
                color: Material.foreground
                font.pixelSize: 11
            }
        }
    }
}
