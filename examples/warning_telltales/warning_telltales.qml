import QtQuick 2.15

Rectangle {
    color: "#1a1a2e"

    Image {
        id: oilLamp
        visible: false
        source: "assets/dot_red.png"
        x: 24
        y: 24
        width: 32
        height: 32
        fillMode: Image.PreserveAspectFit
    }
    Image {
        id: coolantLamp
        visible: false
        source: "assets/dot_amber.png"
        x: 64
        y: 24
        width: 32
        height: 32
    }
    Image {
        id: absLamp
        visible: false
        source: "assets/dot_green.png"
        x: 104
        y: 24
        width: 32
        height: 32
    }
    Text {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 8
        color: "#888888"
        font.pixelSize: 14
        text: "warnings"
    }
}
