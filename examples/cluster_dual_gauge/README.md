# cluster_dual_gauge

Dual Arc cluster demo with `speed_kmh` and `rpm` module properties.

## Preview

```bash
qvglc run cluster_dual_gauge.qml --profile profiles/cluster_480x272.yaml \
  --set speed_kmh=120 --set rpm=3500
```

## Vehicle / CAN path

`vehicle_bindings.yaml` maps `qvgl_vehicle_state_t` fields to generated setters.
`qvglc compile` emits `qvgl_cluster_dual_gauge_vehicle.h` automatically when the YAML is present.

Demo CAN frame **0x200** (little-endian):

| Offset | Field        | Encoding      |
|--------|--------------|---------------|
| 0–1    | speed_kmh    | uint16 × 0.1  |
| 2–3    | rpm          | uint16        |
| 4      | gear         | uint8         |
| 5      | warnings     | uint8 bitmask |

```bash
qvglc run cluster_dual_gauge.qml --profile profiles/cluster_480x272.yaml \
  --can 0x200:1405A00F --headless --exit --loop-frames 5
```

See [can_demo.yaml](can_demo.yaml) for more frames.

## MCU loop

```c
#include "qvgl/qvgl_vehicle_model.h"
#include "qvgl_cluster_dual_gauge_vehicle.h"

qvgl_vehicle_state_t vs;
qvgl_vehicle_state_init(&vs);

void on_can_rx(uint32_t id, const uint8_t *data, uint8_t dlc)
{
    if (qvgl_vehicle_decode_demo_can(id, data, dlc, &vs))
        qvgl_cluster_dual_gauge_apply_vehicle(&ui, &vs);
}
```
