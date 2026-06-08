import QtQuick 2.15

Item {
    width: 280
    height: 160

    property real level: 0.5
    property int channel: 1
    property bool alarm: false
    property string title: "Ia"

    Rectangle {
        anchors.fill: parent
        color: "#18191c"
        radius: 8
    }

    Text {
        id: titleLabel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 12
        text: title
        color: "#e8e8e8"
        font.pixelSize: 16
    }

    Text {
        id: channelLabel
        anchors.top: titleLabel.bottom
        anchors.topMargin: 6
        anchors.left: parent.left
        anchors.margins: 12
        text: channel
        color: "#9aa0a6"
        font.pixelSize: 14
    }

    Rectangle {
        id: alarmBar
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.margins: 16
        width: 200
        height: 10
        radius: 5
        color: "#ff5252"
        visible: alarm
        opacity: level
    }
}
