#ifndef QVGL_PLOT_LVGL_H
#define QVGL_PLOT_LVGL_H

#include "qvgl/qvgl_plot.h"

#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    lv_obj_t * chart;
    lv_chart_series_t * series;
    lv_obj_t * x_labels[QVGL_PLOT_MAX_TICKS];
    lv_obj_t * y_labels[QVGL_PLOT_MAX_TICKS];
    uint8_t tick_count;
    int16_t chart_x;
    int16_t chart_y;
    int16_t chart_w;
    int16_t chart_h;
    float x_min;
    float x_max;
    float y_min;
    float y_max;
    lv_obj_t * cross_v;
    lv_obj_t * cross_h;
    lv_obj_t * cursor_label;
    int32_t x_scratch[QVGL_PLOT_MAX_POINTS];
    int32_t y_scratch[QVGL_PLOT_MAX_POINTS];
    size_t point_count;
} qvgl_plot_t;

void qvgl_plot_set_domain(qvgl_plot_t * plot, float x_min, float x_max, float y_min, float y_max);

void qvgl_plot_set_points(qvgl_plot_t * plot, const qvgl_plot_point_t * pts, size_t count);

void qvgl_plot_apply_series(
    qvgl_plot_t * plot,
    const qvgl_plot_point_t * pts,
    size_t count,
    float time_min,
    float time_max,
    float empty_min_y,
    float empty_max_y);

void qvgl_plot_set_crosshair(qvgl_plot_t * plot, float t_sec, float y_val);

void qvgl_plot_clear_crosshair(qvgl_plot_t * plot);

void qvgl_plot_set_cursor(qvgl_plot_t * plot, float t_sec, float y_val);

#ifdef __cplusplus
}
#endif

#endif /* QVGL_PLOT_LVGL_H */
