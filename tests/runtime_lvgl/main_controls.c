#include "qvgl_preview_display.h"
#include "qvgl_test.h"

#include "lvgl.h"

void test_controls_set_enabled(void);
void test_controls_set_checked(void);
void test_controls_set_slider_value(void);
void test_controls_set_dropdown_index(void);
void test_controls_set_progress_value(void);

int main(void)
{
    lv_init();
    lv_display_t * disp = qvgl_preview_display_create(320, 240);
    if(!disp) return EXIT_FAILURE;
    lv_display_set_default(disp);

    QVGL_TEST_RUN(test_controls_set_enabled);
    QVGL_TEST_RUN(test_controls_set_checked);
    QVGL_TEST_RUN(test_controls_set_slider_value);
    QVGL_TEST_RUN(test_controls_set_dropdown_index);
    QVGL_TEST_RUN(test_controls_set_progress_value);

    lv_display_delete(disp);
    lv_deinit();
    return EXIT_SUCCESS;
}
