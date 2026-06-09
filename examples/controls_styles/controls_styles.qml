import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

Item {
    width: 320
    height: 280

    property bool panelEnabled: true
    property real panelOpacity: 1.0

    Rectangle {
        anchors.fill: parent
        color: Material.background
        radius: 8

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            Label {
                text: "Panel state"
                color: Material.foreground
                font.pixelSize: 14
            }

            Slider {
                id: dimSlider
                Layout.fillWidth: true
                from: 0.3
                to: 1.0
                value: panelOpacity
                enabled: panelEnabled
                onMoved: app_on_dim_moved()
            }

            Switch {
                id: enableSwitch
                checked: panelEnabled
                onClicked: app_on_panel_toggled()
                onPressed: app_on_enable_pressed()
                onReleased: app_on_enable_released()
            }

            Button {
                id: actionBtn
                Layout.fillWidth: true
                text: "Action"
                enabled: panelEnabled
                opacity: panelOpacity
                onClicked: app_on_action_clicked()
            }

            CheckBox {
                text: "Dim when disabled"
                checked: false
                enabled: panelEnabled
                opacity: panelOpacity
            }
        }
    }
}
