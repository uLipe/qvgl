#include "qvgl/qvgl_controls.h"
#include "qvgl_test.h"

void test_controls_set_enabled(void)
{
    lv_obj_t * btn = lv_button_create(lv_screen_active());
    qvgl_controls_set_enabled(btn, false);
    QVGL_ASSERT(lv_obj_has_state(btn, LV_STATE_DISABLED));
    qvgl_controls_set_enabled(btn, true);
    QVGL_ASSERT(!lv_obj_has_state(btn, LV_STATE_DISABLED));
}

void test_controls_set_checked(void)
{
    lv_obj_t * sw = lv_switch_create(lv_screen_active());
    qvgl_controls_set_checked(sw, true);
    QVGL_ASSERT(lv_obj_has_state(sw, LV_STATE_CHECKED));
    qvgl_controls_set_checked(sw, false);
    QVGL_ASSERT(!lv_obj_has_state(sw, LV_STATE_CHECKED));
}

void test_controls_set_slider_value(void)
{
    lv_obj_t * slider = lv_slider_create(lv_screen_active());
    lv_slider_set_range(slider, 0, 100);
    qvgl_controls_set_slider_value(slider, 0.5f, 0.0f, 1.0f);
    QVGL_ASSERT(lv_slider_get_value(slider) == 50);
}

void test_controls_set_dropdown_index(void)
{
    lv_obj_t * dd = lv_dropdown_create(lv_screen_active());
    lv_dropdown_set_options(dd, "A\nB\nC");
    qvgl_controls_set_dropdown_index(dd, 2);
    QVGL_ASSERT(lv_dropdown_get_selected(dd) == 2);
}

void test_controls_set_progress_value(void)
{
    lv_obj_t * bar = lv_bar_create(lv_screen_active());
    lv_bar_set_range(bar, 0, 100);
    qvgl_controls_set_progress_value(bar, 0.75f, 0.0f, 1.0f);
    QVGL_ASSERT(lv_bar_get_value(bar) == 75);
}
