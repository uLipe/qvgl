/**
 * @file qvgl_vehicle_model.h
 * Shared vehicle state for cluster UIs. App/CAN feeds this struct;
 * generated apply helpers map fields to module property setters.
 */
#ifndef QVGL_VEHICLE_MODEL_H
#define QVGL_VEHICLE_MODEL_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define QVGL_VEHICLE_DEMO_CAN_SPEED_RPM 0x200u

#define QVGL_WARN_OIL_PRESSURE (1u << 0)
#define QVGL_WARN_COOLANT      (1u << 1)
#define QVGL_WARN_ABS          (1u << 2)
#define QVGL_WARN_LEFT_BLINK   (1u << 3)
#define QVGL_WARN_RIGHT_BLINK  (1u << 4)

typedef struct {
    float speed_kmh;
    float rpm;
    uint8_t gear;
    uint32_t warnings;
} qvgl_vehicle_state_t;

void qvgl_vehicle_state_init(qvgl_vehicle_state_t * st);

/** Demo CAN layout: ID 0x200, DLC>=4 — speed 0.1 km/h LE @0, rpm LE @2. */
bool qvgl_vehicle_decode_demo_can(
    uint32_t can_id,
    const uint8_t * data,
    uint8_t dlc,
    qvgl_vehicle_state_t * st);

#ifdef __cplusplus
}
#endif

#endif /* QVGL_VEHICLE_MODEL_H */
