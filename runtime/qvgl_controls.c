#include "qvgl/qvgl_controls.h"
#include "qvgl/qvgl_widget.h"

void qvgl_controls_set_slider_value(lv_obj_t * slider, float value, float vmin, float vmax)
{
    qvgl_widget_set_slider_value(slider, value, vmin, vmax);
}

void qvgl_controls_set_checked(lv_obj_t * obj, bool checked)
{
    qvgl_widget_set_checked(obj, checked);
}

void qvgl_controls_set_enabled(lv_obj_t * obj, bool enabled)
{
    qvgl_widget_set_enabled(obj, enabled);
}

void qvgl_controls_set_dropdown_index(lv_obj_t * dropdown, int32_t index)
{
    qvgl_widget_set_dropdown_selected(dropdown, index);
}

void qvgl_controls_set_progress_value(lv_obj_t * bar, float value, float vmin, float vmax)
{
    qvgl_widget_set_bar_value(bar, value, vmin, vmax);
}
