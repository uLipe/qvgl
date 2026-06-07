import QtQuick 2.15

// One module property drives label text
Item {
    id: root
    width: 200
    height: 100

    property real value: 42.0

    Text {
        id: valueLabel
        anchors.centerIn: parent
        text: value
        color: "#00d4aa"
        font.pixelSize: 18
    }
}
