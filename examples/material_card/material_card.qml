import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material

Rectangle {
    width: 320
    height: 120
    color: Material.background
    radius: 8

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 6
        color: Material.accent
        radius: 8
    }

    Text {
        id: titleLabel
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 28
        text: "Material L1"
        color: Material.foreground
        font.pixelSize: 16
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: titleLabel.bottom
        anchors.topMargin: 6
        text: "primary token"
        color: Material.primary
        font.pixelSize: 12
    }
}
