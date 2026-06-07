import QtQuick 2.15

// Static layout card — no bindings
Item {
    id: root
    width: 320
    height: 240

    Rectangle {
        anchors.fill: parent
        color: "#2d2d30"
        radius: 8
        border.width: 2
        border.color: "#505050"
    }

    Text {
        anchors.centerIn: parent
        text: "Hello QVGL"
        color: "#ffffff"
        font.pixelSize: 24
        horizontalAlignment: Text.AlignHCenter
    }
}
