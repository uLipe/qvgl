// Trimmed static snapshot of Qt for MCUs instrument_cluster.qml (bindings → literals).
import QtQuick 2.15

Rectangle {
    color: "#00414A"
    Text {
        id: speedometer
        color: "#2CDE85"
        anchors.centerIn: parent
        font.pixelSize: 90
        text: "0"
    }
    Text {
        color: "#28C878"
        anchors.horizontalCenter: speedometer.horizontalCenter
        anchors.bottom: speedometer.top
        anchors.bottomMargin: -36
        font.pixelSize: 22
        text: "km/h"
    }
    Text {
        id: tripMeter
        color: "#2CDE85"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 5
        font.pixelSize: 24
        text: "0.0 km"
    }
    Text {
        color: "#28C878"
        anchors.horizontalCenter: speedometer.horizontalCenter
        anchors.bottom: tripMeter.top
        anchors.bottomMargin: -6
        font.pixelSize: 22
        text: "Trip"
    }
    Text {
        opacity: 0.0
        color: "#2CDE85"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.topMargin: 20
        anchors.leftMargin: 40
        font.pixelSize: 60
        text: "<"
    }
    Text {
        opacity: 0.0
        color: "#2CDE85"
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 20
        anchors.rightMargin: 40
        font.pixelSize: 60
        text: ">"
    }
}
