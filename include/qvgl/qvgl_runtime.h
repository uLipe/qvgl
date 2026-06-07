/**
 * @file qvgl_runtime.h
 * Small runtime shared by SDL preview and MCU builds (hand-written; not generated).
 */
#ifndef QVGL_RUNTIME_H
#define QVGL_RUNTIME_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void qvgl_runtime_init(void);

float qvgl_map_linear_f32(float v, float in_min, float in_max, float out_min, float out_max);

#ifdef __cplusplus
}
#endif

#endif /* QVGL_RUNTIME_H */
