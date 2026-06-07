import QtQuick 2.15

Item {
    id: root
    width: 480
    height: 272

    Rectangle {
        id: header
        height: 40
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        color: "#1a1a2e"
    }

    Text {
        anchors.centerIn: header
        text: "CLUSTER"
        color: "#ffffff"
        font.pixelSize: 18
    }

    Rectangle {
        id: gauge_left
        width: 120
        height: 120
        anchors.left: parent.left
        anchors.top: header.bottom
        anchors.leftMargin: 24
        anchors.topMargin: 16
        color: "#2d2d30"
        radius: 8
    }

    Rectangle {
        id: gauge_right
        width: 120
        height: 120
        anchors.right: parent.right
        anchors.top: header.bottom
        anchors.rightMargin: 24
        anchors.topMargin: 16
        color: "#2d2d30"
        radius: 8
    }

    Rectangle {
        id: footer
        height: 32
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        color: "#111122"
    }

    Text {
        anchors.centerIn: footer
        text: "PRND — static"
        color: "#888888"
        font.pixelSize: 14
    }
}
