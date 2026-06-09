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
void test_plot_set_points(void);
void test_plot_set_domain_labels(void);
void test_plot_set_cursor(void);
void test_plot_apply_series(void);
void test_plot_relayout(void);
void test_plot_clear_crosshair(void);
void test_bound_setters_title(void);

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
    QVGL_TEST_RUN(test_plot_set_points);
    QVGL_TEST_RUN(test_plot_set_domain_labels);
    QVGL_TEST_RUN(test_plot_set_cursor);
    QVGL_TEST_RUN(test_plot_apply_series);
    QVGL_TEST_RUN(test_plot_relayout);
    QVGL_TEST_RUN(test_plot_clear_crosshair);
    QVGL_TEST_RUN(test_bound_setters_title);

    lv_display_delete(disp);
    lv_deinit();
    return EXIT_SUCCESS;
}
