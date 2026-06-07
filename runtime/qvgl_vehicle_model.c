#include "qvgl/qvgl_vehicle_model.h"

#include <string.h>

void qvgl_vehicle_state_init(qvgl_vehicle_state_t * st)
{
    if(!st) return;
    memset(st, 0, sizeof(*st));
}

bool qvgl_vehicle_decode_demo_can(
    uint32_t can_id,
    const uint8_t * data,
    uint8_t dlc,
    qvgl_vehicle_state_t * st)
{
    if(!st || !data || dlc < 4) return false;
    if(can_id != QVGL_VEHICLE_DEMO_CAN_SPEED_RPM) return false;

    uint16_t speed_raw = (uint16_t)data[0] | ((uint16_t)data[1] << 8);
    uint16_t rpm_raw = (uint16_t)data[2] | ((uint16_t)data[3] << 8);
    st->speed_kmh = (float)speed_raw * 0.1f;
    st->rpm = (float)rpm_raw;
    if(dlc >= 5) st->gear = data[4];
    if(dlc >= 6) st->warnings = (uint32_t)data[5];
    return true;
}
