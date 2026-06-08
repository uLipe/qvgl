import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

Item {
    width: 480
    height: 300

    property string cursorText: ""

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
                    color: "#4fc3f7"
                }

                Label {
                    text: "Phase current Ia"
                    Layout.fillWidth: true
                    color: Material.foreground
                    font.pixelSize: 14
                }

                Label {
                    text: "A"
                    color: "#4fc3f7"
                    font.pixelSize: 12
                }

                ToolButton {
                    id: closeBtn
                    text: "X"
                    onClicked: app_on_plot_close()
                }
            }

            LinePlot {
                Layout.fillWidth: true
                Layout.fillHeight: true
                hoverEnabled: true
                lineColor: "#4fc3f7"
                gridDiv: 4
                xMin: 0
                xMax: 5
                yMin: -1.1
                yMax: 1.3
                yUnit: "A"
                xUnit: "t (s)"

                PlotPoint { x: 0.0
                    y: 0.2 }
                PlotPoint { x: 0.5
                    y: 0.8 }
                PlotPoint { x: 1.0
                    y: 1.1 }
                PlotPoint { x: 1.5
                    y: 0.4 }
                PlotPoint { x: 2.0
                    y: -0.3 }
                PlotPoint { x: 2.5
                    y: -0.9 }
                PlotPoint { x: 3.0
                    y: -0.5 }
                PlotPoint { x: 3.5
                    y: 0.6 }
                PlotPoint { x: 4.0
                    y: 1.0 }
                PlotPoint { x: 4.5
                    y: 0.3 }
                PlotPoint { x: 5.0
                    y: -0.2 }
            }

            Label {
                id: cursorLabel
                text: cursorText
                color: Material.foreground
                font.pixelSize: 11
            }
        }
    }
}
