#include "qvgl/qvgl_widget.h"

#include <math.h>

void qvgl_widget_set_text(lv_obj_t * label, const char * text)
{
    if(!label) return;
    lv_label_set_text(label, text ? text : "");
}

void qvgl_widget_set_visible(lv_obj_t * obj, bool visible)
{
    if(!obj) return;
    if(visible)
        lv_obj_remove_flag(obj, LV_OBJ_FLAG_HIDDEN);
    else
        lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN);
}

void qvgl_widget_set_opa(lv_obj_t * obj, lv_opa_t opa)
{
    if(!obj) return;
    lv_obj_set_style_opa(obj, opa, LV_PART_MAIN);
}

void qvgl_widget_set_opa_f32(lv_obj_t * obj, float opa)
{
    if(!obj) return;
    if(opa <= 0.0f) {
        lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN);
        return;
    }
    lv_obj_remove_flag(obj, LV_OBJ_FLAG_HIDDEN);
    if(opa > 1.0f) opa = 1.0f;
    lv_obj_set_style_opa(obj, (lv_opa_t)lroundf(opa * 255.0f), LV_PART_MAIN);
}

int32_t qvgl_widget_arc_value_for(lv_obj_t * arc, float value, float vmin, float vmax)
{
    if(!arc) return 0;
    int32_t arc_min = lv_arc_get_min_value(arc);
    int32_t arc_max = lv_arc_get_max_value(arc);
    if(vmax == vmin) return arc_min;
    float t = (value - vmin) / (vmax - vmin);
    int32_t arc_val = (int32_t)lroundf((float)arc_min + t * (float)(arc_max - arc_min));
    if(arc_val < arc_min) arc_val = arc_min;
    if(arc_val > arc_max) arc_val = arc_max;
    return arc_val;
}

void qvgl_widget_set_arc_i32(lv_obj_t * arc, int32_t value)
{
    if(!arc) return;
    int32_t mn = lv_arc_get_min_value(arc);
    int32_t mx = lv_arc_get_max_value(arc);
    if(value < mn) value = mn;
    if(value > mx) value = mx;
    lv_arc_set_value(arc, value);
}

void qvgl_widget_set_arc_value(lv_obj_t * arc, float value, float vmin, float vmax)
{
    qvgl_widget_set_arc_i32(arc, qvgl_widget_arc_value_for(arc, value, vmin, vmax));
}

void qvgl_widget_set_checked(lv_obj_t * obj, bool checked)
{
    if(!obj) return;
    if(checked)
        lv_obj_add_state(obj, LV_STATE_CHECKED);
    else
        lv_obj_clear_state(obj, LV_STATE_CHECKED);
}

void qvgl_widget_set_slider_value(lv_obj_t * slider, float value, float vmin, float vmax)
{
    if(!slider) return;
    int32_t mn = lv_slider_get_min_value(slider);
    int32_t mx = lv_slider_get_max_value(slider);
    if(fabsf(vmax - vmin) < 1e-9f) {
        lv_slider_set_value(slider, mn, LV_ANIM_OFF);
        return;
    }
    float t = (value - vmin) / (vmax - vmin);
    if(t < 0.0f) t = 0.0f;
    if(t > 1.0f) t = 1.0f;
    int32_t v = (int32_t)lroundf((float)mn + t * (float)(mx - mn));
    if(v < mn) v = mn;
    if(v > mx) v = mx;
    lv_slider_set_value(slider, v, LV_ANIM_OFF);
}
