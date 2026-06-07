import QtQuick 2.15

Rectangle {
    color: "#1a1a2e"
    Image {
        source: "assets/dot_red.png"
        x: 24
        y: 24
        width: 32
        height: 32
        fillMode: Image.PreserveAspectFit
    }
    Image {
        source: "assets/dot_green.png"
        x: 56
        y: 24
        width: 16
        height: 16
    }
    Image {
        source: "assets/dot_amber.png"
        x: 88
        y: 24
        width: 16
        height: 16
        opacity: 0.5
    }
    Text {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 8
        color: "#eaeaea"
        font.pixelSize: 14
        text: "icons"
    }
}
