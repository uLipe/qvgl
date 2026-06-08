#include "qvgl/qvgl_widget.h"
#include "qvgl_test.h"

#include <string.h>

void test_widget_text(void)
{
    lv_obj_t * label = lv_label_create(lv_screen_active());
    qvgl_widget_set_text(label, "hello");
    QVGL_ASSERT(strcmp(lv_label_get_text(label), "hello") == 0);
    qvgl_widget_set_text(label, NULL);
    QVGL_ASSERT(strcmp(lv_label_get_text(label), "") == 0);
    qvgl_widget_set_text(NULL, "x");
}

void test_widget_visible(void)
{
    lv_obj_t * box = lv_obj_create(lv_screen_active());
    qvgl_widget_set_visible(box, false);
    QVGL_ASSERT(lv_obj_has_flag(box, LV_OBJ_FLAG_HIDDEN));
    qvgl_widget_set_visible(box, true);
    QVGL_ASSERT(!lv_obj_has_flag(box, LV_OBJ_FLAG_HIDDEN));
}

void test_widget_opa(void)
{
    lv_obj_t * box = lv_obj_create(lv_screen_active());
    qvgl_widget_set_opa(box, LV_OPA_50);
    QVGL_ASSERT(lv_obj_get_style_opa(box, LV_PART_MAIN) == LV_OPA_50);
}

void test_widget_opa_f32(void)
{
    lv_obj_t * box = lv_obj_create(lv_screen_active());
    qvgl_widget_set_opa_f32(box, 0.5f);
    QVGL_ASSERT(lv_obj_get_style_opa(box, LV_PART_MAIN) == LV_OPA_50);
    QVGL_ASSERT(!lv_obj_has_flag(box, LV_OBJ_FLAG_HIDDEN));
    qvgl_widget_set_opa_f32(box, 0.0f);
    QVGL_ASSERT(lv_obj_has_flag(box, LV_OBJ_FLAG_HIDDEN));
}

void test_widget_arc_value(void)
{
    lv_obj_t * arc = lv_arc_create(lv_screen_active());
    lv_arc_set_range(arc, -7, 20);
    qvgl_widget_set_arc_value(arc, 0.5f, -0.7f, 2.0f);
    QVGL_ASSERT(lv_arc_get_value(arc) == 5);
    qvgl_widget_set_arc_value(arc, -1.0f, -0.7f, 2.0f);
    QVGL_ASSERT(lv_arc_get_value(arc) == -7);
    qvgl_widget_set_arc_value(arc, 3.0f, -0.7f, 2.0f);
    QVGL_ASSERT(lv_arc_get_value(arc) == 20);
    QVGL_ASSERT(qvgl_widget_arc_value_for(arc, 0.0f, -0.7f, 2.0f) == 0);
}

void test_widget_slider_value(void)
{
    lv_obj_t * slider = lv_slider_create(lv_screen_active());
    lv_slider_set_range(slider, 0, 1000);
    qvgl_widget_set_slider_value(slider, 0.5f, 0.0f, 1.0f);
    QVGL_ASSERT(lv_slider_get_value(slider) == 500);
    qvgl_widget_set_slider_value(slider, 1.0f, 0.0f, 1.0f);
    QVGL_ASSERT(lv_slider_get_value(slider) == 1000);
}

void test_widget_checked(void)
{
    lv_obj_t * sw = lv_switch_create(lv_screen_active());
    qvgl_widget_set_checked(sw, true);
    QVGL_ASSERT(lv_obj_has_state(sw, LV_STATE_CHECKED));
    qvgl_widget_set_checked(sw, false);
    QVGL_ASSERT(!lv_obj_has_state(sw, LV_STATE_CHECKED));
}
