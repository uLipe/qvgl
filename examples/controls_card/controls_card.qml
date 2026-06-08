import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

Item {
    width: 320
    height: 200

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

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#0d0d0f"
                radius: 4
            }

            Label {
                text: "t=0.0  y=0.0"
                color: Material.foreground
                font.pixelSize: 11
            }
        }
    }
}
