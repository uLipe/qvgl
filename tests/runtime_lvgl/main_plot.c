#include "qvgl_preview_display.h"
#include "qvgl_test.h"

#include "lvgl.h"

void test_plot_set_points(void);
void test_plot_set_domain_labels(void);
void test_plot_set_cursor(void);
void test_plot_apply_series(void);
void test_plot_relayout(void);
void test_plot_clear_crosshair(void);
void test_plot_secondary_series(void);

int main(void)
{
    lv_init();
    lv_display_t * disp = qvgl_preview_display_create(320, 240);
    if(!disp) return EXIT_FAILURE;
    lv_display_set_default(disp);

    QVGL_TEST_RUN(test_plot_set_points);
    QVGL_TEST_RUN(test_plot_set_domain_labels);
    QVGL_TEST_RUN(test_plot_set_cursor);
    QVGL_TEST_RUN(test_plot_apply_series);
    QVGL_TEST_RUN(test_plot_relayout);
    QVGL_TEST_RUN(test_plot_clear_crosshair);
    QVGL_TEST_RUN(test_plot_secondary_series);

    lv_display_delete(disp);
    lv_deinit();
    return EXIT_SUCCESS;
}
