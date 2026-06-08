import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

Item {
    width: 320
    height: 320

    property real gain: 0.5
    property bool outputEnabled: true
    property bool mute: false
    property int preset: 0

    Rectangle {
        anchors.fill: parent
        color: Material.background
        radius: 8

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            Label {
                text: "Gain"
                color: Material.foreground
                font.pixelSize: 14
            }

            Slider {
                id: gainSlider
                Layout.fillWidth: true
                from: 0
                to: 1
                value: gain
                onMoved: app_on_gain_moved()
                onValueChanged: app_on_gain_changed()
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Label {
                    text: "Output"
                    color: Material.foreground
                    font.pixelSize: 14
                    Layout.fillWidth: true
                }

                Switch {
                    id: outputSwitch
                    checked: outputEnabled
                    onClicked: app_on_output_toggled()
                }
            }

            CheckBox {
                id: muteBox
                text: "Mute"
                checked: mute
                onClicked: app_on_mute_toggled()
            }

            ComboBox {
                id: presetBox
                Layout.fillWidth: true
                model: ["Off", "Low", "High"]
                currentIndex: preset
                onActivated: app_on_preset_activated()
            }

            Button {
                id: applyBtn
                Layout.fillWidth: true
                text: "Apply"
                onClicked: app_on_apply_clicked()
            }
        }
    }
}
