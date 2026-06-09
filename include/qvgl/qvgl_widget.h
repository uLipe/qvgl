#ifndef QVGL_WIDGET_H
#define QVGL_WIDGET_H

#include "lvgl.h"

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void qvgl_widget_set_text(lv_obj_t * label, const char * text);
void qvgl_widget_set_visible(lv_obj_t * obj, bool visible);
void qvgl_widget_set_enabled(lv_obj_t * obj, bool enabled);
void qvgl_widget_set_opa(lv_obj_t * obj, lv_opa_t opa);
void qvgl_widget_set_opa_f32(lv_obj_t * obj, float opa);

int32_t qvgl_widget_arc_value_for(lv_obj_t * arc, float value, float vmin, float vmax);
void qvgl_widget_set_arc_i32(lv_obj_t * arc, int32_t value);
void qvgl_widget_set_arc_value(lv_obj_t * arc, float value, float vmin, float vmax);

void qvgl_widget_set_checked(lv_obj_t * obj, bool checked);
void qvgl_widget_set_slider_value(lv_obj_t * slider, float value, float vmin, float vmax);
void qvgl_widget_set_bar_value(lv_obj_t * bar, float value, float vmin, float vmax);
void qvgl_widget_set_dropdown_selected(lv_obj_t * dropdown, int32_t index);

#ifdef __cplusplus
}
#endif

#endif /* QVGL_WIDGET_H */
