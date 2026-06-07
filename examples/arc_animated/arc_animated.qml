import QtQuick 2.15

Item {
    width: 200
    height: 200

    property real level: 0

    Rectangle {
        anchors.fill: parent
        color: "#1a1a2e"
        radius: 8
    }

    Arc {
        id: gauge
        anchors.centerIn: parent
        width: 160
        height: 160
        from: 135
        to: 45
        minValue: 0
        maxValue: 100
        value: level
        lineWidth: 12
        color: "#00d4aa"

        NumberAnimation on value {
            duration: 300
        }
    }

}
