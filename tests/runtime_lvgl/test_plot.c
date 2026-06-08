#include "qvgl/qvgl_plot_lvgl.h"
#include "qvgl_test.h"

#include <string.h>

void test_plot_set_points(void)
{
    lv_obj_t * parent = lv_obj_create(lv_screen_active());
    qvgl_plot_t plot = {0};
    plot.chart_x = 10;
    plot.chart_y = 10;
    plot.chart_w = 200;
    plot.chart_h = 100;
    plot.tick_count = 3;
    plot.chart = lv_chart_create(parent);
    lv_obj_set_size(plot.chart, plot.chart_w, plot.chart_h);
    lv_chart_set_type(plot.chart, LV_CHART_TYPE_SCATTER);
    plot.series = lv_chart_add_series(plot.chart, lv_color_hex(0x4fc3f7), LV_CHART_AXIS_PRIMARY_Y);

    for(int i = 0; i < 3; i++) {
        plot.x_labels[i] = lv_label_create(parent);
        plot.y_labels[i] = lv_label_create(parent);
    }

    qvgl_plot_set_domain(&plot, 0.0f, 10.0f, -1.0f, 1.0f);

    const qvgl_plot_point_t pts[] = {
        {0.0f, 0.0f}, {5.0f, 0.5f}, {10.0f, -0.2f},
    };
    qvgl_plot_set_points(&plot, pts, 3);
    QVGL_ASSERT(plot.point_count == 3);
    QVGL_ASSERT(lv_chart_get_point_count(plot.chart) == 3);

    qvgl_plot_set_points(&plot, pts, 1);
    QVGL_ASSERT(lv_chart_get_point_count(plot.chart) == 1);
}

void test_plot_set_domain_labels(void)
{
    lv_obj_t * parent = lv_obj_create(lv_screen_active());
    qvgl_plot_t plot = {0};
    plot.chart_x = 20;
    plot.chart_y = 20;
    plot.chart_w = 160;
    plot.chart_h = 80;
    plot.tick_count = 2;
    plot.x_labels[0] = lv_label_create(parent);
    plot.x_labels[1] = lv_label_create(parent);
    plot.y_labels[0] = lv_label_create(parent);
    plot.y_labels[1] = lv_label_create(parent);

    qvgl_plot_set_domain(&plot, 0.0f, 4.0f, -2.0f, 2.0f);
    QVGL_ASSERT(strcmp(lv_label_get_text(plot.x_labels[0]), "0.00") == 0);
    QVGL_ASSERT(strcmp(lv_label_get_text(plot.x_labels[1]), "4.00") == 0);

    qvgl_plot_set_domain(&plot, 0.0f, 10.0f, -1.0f, 1.0f);
    QVGL_ASSERT(strcmp(lv_label_get_text(plot.x_labels[1]), "10.0") == 0);
}

void test_plot_set_cursor(void)
{
    lv_obj_t * parent = lv_obj_create(lv_screen_active());
    qvgl_plot_t plot = {0};
    plot.chart_x = 0;
    plot.chart_y = 0;
    plot.chart_w = 100;
    plot.chart_h = 50;
    plot.x_min = 0.0f;
    plot.x_max = 5.0f;
    plot.y_min = -1.0f;
    plot.y_max = 1.0f;
    plot.cursor_label = lv_label_create(parent);
    plot.cross_v = lv_obj_create(parent);
    plot.cross_h = lv_obj_create(parent);
    lv_obj_add_flag(plot.cross_v, LV_OBJ_FLAG_HIDDEN);
    lv_obj_add_flag(plot.cross_h, LV_OBJ_FLAG_HIDDEN);

    qvgl_plot_set_cursor(&plot, 2.5f, 0.0f);
    QVGL_ASSERT(strstr(lv_label_get_text(plot.cursor_label), "t=") != NULL);
    QVGL_ASSERT(!lv_obj_has_flag(plot.cross_v, LV_OBJ_FLAG_HIDDEN));
}

void test_plot_apply_series(void)
{
    lv_obj_t * parent = lv_obj_create(lv_screen_active());
    qvgl_plot_t plot = {0};
    plot.chart_x = 10;
    plot.chart_y = 10;
    plot.chart_w = 200;
    plot.chart_h = 100;
    plot.tick_count = 2;
    plot.chart = lv_chart_create(parent);
    lv_obj_set_size(plot.chart, plot.chart_w, plot.chart_h);
    lv_chart_set_type(plot.chart, LV_CHART_TYPE_SCATTER);
    plot.series = lv_chart_add_series(plot.chart, lv_color_hex(0x4fc3f7), LV_CHART_AXIS_PRIMARY_Y);
    plot.x_labels[0] = lv_label_create(parent);
    plot.x_labels[1] = lv_label_create(parent);
    plot.y_labels[0] = lv_label_create(parent);
    plot.y_labels[1] = lv_label_create(parent);

    const qvgl_plot_point_t pts[] = {
        {0.0f, 0.5f}, {2.5f, -0.8f}, {5.0f, 0.1f},
    };
    qvgl_plot_apply_series(&plot, pts, 3, 0.0f, 5.0f, -1.0f, 1.0f);
    QVGL_ASSERT(plot.point_count == 3);
    QVGL_ASSERT(plot.y_min < -0.8f);
    QVGL_ASSERT(plot.y_max > 0.5f);
}

void test_plot_relayout(void)
{
    lv_obj_t * parent = lv_obj_create(lv_screen_active());
    lv_obj_set_size(parent, 400, 240);
    qvgl_plot_t plot = {0};
    plot.pad_l = 40;
    plot.pad_r = 8;
    plot.pad_t = 8;
    plot.pad_b = 24;
    plot.tick_count = 2;
    plot.chart = lv_chart_create(parent);
    plot.x_labels[0] = lv_label_create(parent);
    plot.x_labels[1] = lv_label_create(parent);
    plot.y_labels[0] = lv_label_create(parent);
    plot.y_labels[1] = lv_label_create(parent);
    plot.series = lv_chart_add_series(plot.chart, lv_color_hex(0x4fc3f7), LV_CHART_AXIS_PRIMARY_Y);
    plot.x_unit_label = lv_label_create(parent);
    plot.axis_bottom = lv_obj_create(parent);
    plot.axis_left = lv_obj_create(parent);
    plot.x_min = 0.0f;
    plot.x_max = 5.0f;
    plot.y_min = -1.0f;
    plot.y_max = 1.0f;

    qvgl_plot_relayout(&plot);
    QVGL_ASSERT(plot.chart_w > 300);
    QVGL_ASSERT(plot.chart_h > 180);
    QVGL_ASSERT(lv_obj_get_width(plot.axis_bottom) == plot.chart_w);
}

void test_plot_clear_crosshair(void)
{
    lv_obj_t * parent = lv_obj_create(lv_screen_active());
    qvgl_plot_t plot = {0};
    plot.chart_x = 0;
    plot.chart_y = 0;
    plot.chart_w = 80;
    plot.chart_h = 40;
    plot.x_min = 0.0f;
    plot.x_max = 5.0f;
    plot.y_min = -1.0f;
    plot.y_max = 1.0f;
    plot.cross_v = lv_obj_create(parent);
    plot.cross_h = lv_obj_create(parent);

    qvgl_plot_set_crosshair(&plot, 2.0f, 0.0f);
    QVGL_ASSERT(!lv_obj_has_flag(plot.cross_v, LV_OBJ_FLAG_HIDDEN));
    qvgl_plot_clear_crosshair(&plot);
    QVGL_ASSERT(lv_obj_has_flag(plot.cross_v, LV_OBJ_FLAG_HIDDEN));
    QVGL_ASSERT(lv_obj_has_flag(plot.cross_h, LV_OBJ_FLAG_HIDDEN));
}
