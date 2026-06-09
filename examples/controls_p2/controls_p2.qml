import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

Item {
    width: 320
    height: 360

    property real loadLevel: 0.65
    property bool ecoMode: true
    property bool sportMode: false

    Rectangle {
        anchors.fill: parent
        color: Material.background
        radius: 8

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            Label {
                text: "Load"
                color: Material.foreground
                font.pixelSize: 14
            }

            ProgressBar {
                id: loadBar
                Layout.fillWidth: true
                from: 0
                to: 1
                value: loadLevel
            }

            GroupBox {
                title: "Drive mode"
                Layout.fillWidth: true
                Layout.preferredHeight: 140

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    anchors.topMargin: 20
                    spacing: 8

                    RadioButton {
                        id: ecoRadio
                        text: "Eco"
                        checked: ecoMode
                        onClicked: app_on_eco_selected()
                    }

                    RadioButton {
                        id: sportRadio
                        text: "Sport"
                        checked: sportMode
                        onClicked: app_on_sport_selected()
                    }
                }
            }
        }
    }
}
