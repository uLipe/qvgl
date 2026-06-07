import QtQuick 2.15

Item {
    id: root
    width: 400
    height: 400

    Rectangle {
        id: header
        width: 120
        height: 40
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.leftMargin: 20
        anchors.topMargin: 16
        color: "#333333"
    }

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: header.bottom
        anchors.bottom: parent.bottom
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        anchors.topMargin: 12
        anchors.bottomMargin: 20
        color: "#222222"
    }
}
