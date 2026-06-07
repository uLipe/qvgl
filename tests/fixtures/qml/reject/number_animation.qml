import QtQuick 2.15

Rectangle {
    width: 100
    height: 100
    color: "#ff0000"

    NumberAnimation on opacity {
        to: 0
        duration: 500
    }
}
