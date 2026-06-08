import QtQuick 2.15

Rectangle {
    width: 480
    height: 80
    color: "#1a1a2e"

    property bool oilVisible: false
    property bool coolantVisible: false
    property bool absVisible: false

    Image {
        id: oilLamp
        visible: oilVisible
        source: "assets/dot_red.png"
        x: 24
        y: 24
        width: 32
        height: 32
        fillMode: Image.PreserveAspectFit
    }
    Image {
        id: coolantLamp
        visible: coolantVisible
        source: "assets/dot_amber.png"
        x: 64
        y: 24
        width: 32
        height: 32
    }
    Image {
        id: absLamp
        visible: absVisible
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
