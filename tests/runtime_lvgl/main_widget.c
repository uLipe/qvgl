#include "qvgl_preview_display.h"
#include "qvgl_test.h"

#include "lvgl.h"

void test_widget_text(void);
void test_widget_visible(void);
void test_widget_opa(void);
void test_widget_opa_f32(void);
void test_widget_arc_value(void);
void test_widget_slider_value(void);
void test_widget_checked(void);
void test_widget_enabled(void);

int main(void)
{
    lv_init();
    lv_display_t * disp = qvgl_preview_display_create(320, 240);
    if(!disp) return EXIT_FAILURE;
    lv_display_set_default(disp);

    QVGL_TEST_RUN(test_widget_text);
    QVGL_TEST_RUN(test_widget_visible);
    QVGL_TEST_RUN(test_widget_opa);
    QVGL_TEST_RUN(test_widget_opa_f32);
    QVGL_TEST_RUN(test_widget_arc_value);
    QVGL_TEST_RUN(test_widget_slider_value);
    QVGL_TEST_RUN(test_widget_checked);
    QVGL_TEST_RUN(test_widget_enabled);

    lv_display_delete(disp);
    lv_deinit();
    return EXIT_SUCCESS;
}
