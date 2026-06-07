import QtQuick 2.15

Item {
    id: root
    width: 480
    height: 272

    property real speed_kmh: 0
    property real rpm: 0

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
        text: "DUAL GAUGE"
        color: "#ffffff"
        font.pixelSize: 18
    }

    Arc {
        id: speedArc
        width: 120
        height: 120
        anchors.left: parent.left
        anchors.top: header.bottom
        anchors.leftMargin: 24
        anchors.topMargin: 16
        from: 210
        to: -30
        minValue: 0
        maxValue: 260
        value: speed_kmh
        lineWidth: 12
        color: "#00d4aa"
    }

    Text {
        id: speedLabel
        anchors.centerIn: speedArc
        text: speed_kmh.toFixed(0) + ""
        color: "#ffffff"
        font.pixelSize: 24
    }

    Arc {
        id: rpmArc
        width: 120
        height: 120
        anchors.right: parent.right
        anchors.top: header.bottom
        anchors.rightMargin: 24
        anchors.topMargin: 16
        from: 210
        to: -30
        minValue: 0
        maxValue: 8000
        value: rpm
        lineWidth: 12
        color: "#ff6b6b"
    }

    Text {
        id: rpmLabel
        anchors.centerIn: rpmArc
        text: rpm.toFixed(0) + ""
        color: "#ffffff"
        font.pixelSize: 24
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
        text: "km/h — rpm"
        color: "#888888"
        font.pixelSize: 14
    }
}
