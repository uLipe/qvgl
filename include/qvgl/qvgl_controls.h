#ifndef QVGL_CONTROLS_H
#define QVGL_CONTROLS_H

#include "lvgl.h"

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void qvgl_controls_set_slider_value(lv_obj_t * slider, float value, float vmin, float vmax);
void qvgl_controls_set_checked(lv_obj_t * obj, bool checked);
void qvgl_controls_set_enabled(lv_obj_t * obj, bool enabled);
void qvgl_controls_set_dropdown_index(lv_obj_t * dropdown, int32_t index);

#ifdef __cplusplus
}
#endif

#endif /* QVGL_CONTROLS_H */
