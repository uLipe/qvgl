import QtQuick 2.15

Item {
    id: root
    width: 400
    height: 400

    property real pressure: 0.5

    Rectangle {
        anchors.fill: parent
        color: "#1a1a2e"
        radius: 16
    }

    Arc {
        id: gaugeArc
        anchors.centerIn: parent
        width: 320
        height: 320
        from: 210
        to: -30
        minValue: -0.7
        maxValue: 2.0
        value: pressure
        lineWidth: 24
        color: "#00d4aa"
        tickCount: 28
        majorTickEvery: 4
        showTickLabels: true
    }

    Text {
        id: valueLabel
        anchors.centerIn: parent
        text: pressure.toFixed(1) + " bar"
        color: "#ffffff"
        font.pixelSize: 36
        horizontalAlignment: Text.AlignHCenter
    }

    Text {
        anchors.bottom: valueLabel.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 8
        text: "TURBO"
        color: "#888888"
        font.pixelSize: 14
    }
}
