#include "qvgl/qvgl_plot_lvgl.h"
#include "qvgl/qvgl_widget.h"

#include <math.h>
#include <stdio.h>

static void refresh_axis_labels(qvgl_plot_t * plot)
{
    if(!plot || plot->tick_count == 0) return;
    float x_span = plot->x_max - plot->x_min;
    float y_span = plot->y_max - plot->y_min;
    if(fabsf(x_span) < 1e-9f) x_span = 1.0f;
    if(fabsf(y_span) < 1e-9f) y_span = 1.0f;

    uint8_t n = plot->tick_count;
    for(uint8_t i = 0; i < n; i++) {
        float t = (n == 1) ? 0.0f : (float)i / (float)(n - 1);
        float tx = plot->x_min + t * x_span;
        float ty = plot->y_max - t * y_span;
        int xx = plot->chart_x + (int)(t * (float)plot->chart_w);
        int yy = plot->chart_y + (int)(t * (float)plot->chart_h);
        char buf[24];

        if(plot->x_labels[i]) {
            qvgl_plot_format_axis(tx, buf, sizeof(buf));
            qvgl_widget_set_text(plot->x_labels[i], buf);
            lv_obj_set_pos(plot->x_labels[i], xx - 16, plot->chart_y + plot->chart_h + 4);
        }
        if(plot->y_labels[i]) {
            qvgl_plot_format_axis(ty, buf, sizeof(buf));
            qvgl_widget_set_text(plot->y_labels[i], buf);
            lv_obj_set_pos(plot->y_labels[i], plot->chart_x > 44 ? plot->chart_x - 44 : 2, yy - 6);
        }
    }
}

void qvgl_plot_set_domain(qvgl_plot_t * plot, float x_min, float x_max, float y_min, float y_max)
{
    if(!plot) return;
    plot->x_min = x_min;
    plot->x_max = x_max;
    plot->y_min = y_min;
    plot->y_max = y_max;

    if(plot->chart) {
        lv_chart_set_axis_range(plot->chart, LV_CHART_AXIS_PRIMARY_X, qvgl_plot_scale_f32(x_min),
                                qvgl_plot_scale_f32(x_max));
        lv_chart_set_axis_range(plot->chart, LV_CHART_AXIS_PRIMARY_Y, qvgl_plot_scale_f32(y_min),
                                qvgl_plot_scale_f32(y_max));
    }
    refresh_axis_labels(plot);
}

void qvgl_plot_set_points(qvgl_plot_t * plot, const qvgl_plot_point_t * pts, size_t count)
{
    if(!plot || !plot->chart) return;
    if(!pts) count = 0;
    if(count > QVGL_PLOT_MAX_POINTS) count = QVGL_PLOT_MAX_POINTS;

    for(size_t i = 0; i < count; i++) {
        plot->x_scratch[i] = qvgl_plot_scale_f32(pts[i].x);
        plot->y_scratch[i] = qvgl_plot_scale_f32(pts[i].y);
    }
    plot->point_count = count;

    lv_chart_set_point_count(plot->chart, (uint32_t)count);
    if(count == 0 || !plot->series) return;
    lv_chart_set_series_values2(plot->chart, plot->series, plot->x_scratch, plot->y_scratch, (uint32_t)count);
    lv_chart_refresh(plot->chart);
}

void qvgl_plot_apply_series(
    qvgl_plot_t * plot,
    const qvgl_plot_point_t * pts,
    size_t count,
    float time_min,
    float time_max,
    float empty_min_y,
    float empty_max_y)
{
    if(!plot) return;
    qvgl_plot_domain_t d =
        qvgl_plot_compute_domain(pts, count, time_min, time_max, empty_min_y, empty_max_y);
    qvgl_plot_set_points(plot, pts, count);
    qvgl_plot_set_domain(plot, d.min_x, d.max_x, d.min_y, d.max_y);
}

static void position_crosshair(qvgl_plot_t * plot, float t_sec, float y_val)
{
    if(!plot || !plot->cross_v || !plot->cross_h) return;

    float x_span = plot->x_max - plot->x_min;
    float y_span = plot->y_max - plot->y_min;
    if(fabsf(x_span) < 1e-9f) x_span = 1.0f;
    if(fabsf(y_span) < 1e-9f) y_span = 1.0f;

    int cx = plot->chart_x + (int)((t_sec - plot->x_min) / x_span * (float)plot->chart_w);
    int cy = plot->chart_y + (int)((plot->y_max - y_val) / y_span * (float)plot->chart_h);

    lv_obj_set_pos(plot->cross_v, cx, plot->chart_y);
    lv_obj_set_size(plot->cross_v, 1, (int32_t)plot->chart_h);
    lv_obj_clear_flag(plot->cross_v, LV_OBJ_FLAG_HIDDEN);
    lv_obj_set_pos(plot->cross_h, plot->chart_x, cy);
    lv_obj_set_size(plot->cross_h, (int32_t)plot->chart_w, 1);
    lv_obj_clear_flag(plot->cross_h, LV_OBJ_FLAG_HIDDEN);
}

void qvgl_plot_set_crosshair(qvgl_plot_t * plot, float t_sec, float y_val)
{
    position_crosshair(plot, t_sec, y_val);
}

void qvgl_plot_clear_crosshair(qvgl_plot_t * plot)
{
    if(!plot) return;
    if(plot->cross_v) lv_obj_add_flag(plot->cross_v, LV_OBJ_FLAG_HIDDEN);
    if(plot->cross_h) lv_obj_add_flag(plot->cross_h, LV_OBJ_FLAG_HIDDEN);
}

void qvgl_plot_set_cursor(qvgl_plot_t * plot, float t_sec, float y_val)
{
    if(!plot) return;

    char ts[24];
    char ys[24];
    char buf[64];
    qvgl_plot_format_axis(t_sec, ts, sizeof(ts));
    qvgl_plot_format_axis(y_val, ys, sizeof(ys));
    snprintf(buf, sizeof(buf), "t=%s  y=%s", ts, ys);
    if(plot->cursor_label) qvgl_widget_set_text(plot->cursor_label, buf);

    qvgl_plot_set_crosshair(plot, t_sec, y_val);
}

void qvgl_plot_relayout(qvgl_plot_t * plot)
{
    if(!plot || !plot->chart) return;

    lv_obj_t * container = lv_obj_get_parent(plot->chart);
    if(!container) return;

    int cw = lv_obj_get_width(container);
    int ch = lv_obj_get_height(container);
    if(cw < plot->pad_l + plot->pad_r + 8) cw = plot->pad_l + plot->pad_r + 8;
    if(ch < plot->pad_t + plot->pad_b + 8) ch = plot->pad_t + plot->pad_b + 8;

    plot->chart_x = plot->pad_l;
    plot->chart_y = plot->pad_t;
    plot->chart_w = cw - plot->pad_l - plot->pad_r;
    plot->chart_h = ch - plot->pad_t - plot->pad_b;
    if(plot->chart_w < 1) plot->chart_w = 1;
    if(plot->chart_h < 1) plot->chart_h = 1;

    lv_obj_set_size(plot->chart, plot->chart_w, plot->chart_h);
    lv_obj_set_pos(plot->chart, plot->chart_x, plot->chart_y);

    if(plot->hit) {
        lv_obj_set_size(plot->hit, plot->chart_w, plot->chart_h);
        lv_obj_set_pos(plot->hit, plot->chart_x, plot->chart_y);
    }

    if(plot->axis_bottom) {
        lv_obj_set_size(plot->axis_bottom, plot->chart_w, 2);
        lv_obj_set_pos(plot->axis_bottom, plot->chart_x, plot->chart_y + plot->chart_h - 1);
    }
    if(plot->axis_left) {
        lv_obj_set_size(plot->axis_left, 2, plot->chart_h);
        lv_obj_set_pos(plot->axis_left, plot->chart_x, plot->chart_y);
    }
    if(plot->x_unit_label) {
        int ux = plot->chart_x + plot->chart_w - 36;
        if(ux < plot->chart_x) ux = plot->chart_x;
        lv_obj_set_pos(plot->x_unit_label, ux, plot->chart_y + plot->chart_h + 4);
    }
    if(plot->y_unit_label)
        lv_obj_set_pos(plot->y_unit_label, 2, plot->chart_y + 6);

    refresh_axis_labels(plot);
}
