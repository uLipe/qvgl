import QtQuick 2.15

Rectangle {
    color: Theme.surface
    Rectangle {
        anchors.centerIn: parent
        width: 160
        height: 56
        color: Theme.accent
        border.width: 2
        border.color: Theme.accent_dim
        radius: 6
    }
    Text {
        anchors.centerIn: parent
        color: Theme.surface
        font.pixelSize: 18
        text: "OK"
    }
}
