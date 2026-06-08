#include "qvgl/qvgl_plot.h"

#include <math.h>
#include <stdio.h>

int32_t qvgl_plot_scale_f32(float v)
{
    return (int32_t)lroundf(v * (float)QVGL_PLOT_SCALE);
}

void qvgl_plot_format_axis(float v, char * buf, size_t buf_len)
{
    if(!buf || buf_len == 0) return;
    float a = fabsf(v);
    if(a >= 1000.0f)
        snprintf(buf, buf_len, "%.1e", (double)v);
    else if(a >= 100.0f)
        snprintf(buf, buf_len, "%.0f", (double)v);
    else if(a >= 10.0f)
        snprintf(buf, buf_len, "%.1f", (double)v);
    else if(a >= 1.0f)
        snprintf(buf, buf_len, "%.2f", (double)v);
    else
        snprintf(buf, buf_len, "%.3f", (double)v);
}

qvgl_plot_domain_t qvgl_plot_compute_domain(
    const qvgl_plot_point_t * pts,
    size_t count,
    float time_min,
    float time_max,
    float empty_min_y,
    float empty_max_y)
{
    qvgl_plot_domain_t d;
    d.min_x = time_min;
    d.max_x = time_max;
    if((d.max_x - d.min_x) < 1e-9f)
        d.max_x = d.min_x + 1.0f;

    int found = 0;
    float min_y = 0.0f;
    float max_y = 0.0f;
    for(size_t i = 0; i < count; i++) {
        if(pts[i].x < time_min || pts[i].x > time_max)
            continue;
        if(!found) {
            min_y = pts[i].y;
            max_y = pts[i].y;
            found = 1;
        }
        else {
            if(pts[i].y < min_y) min_y = pts[i].y;
            if(pts[i].y > max_y) max_y = pts[i].y;
        }
    }

    if(!found) {
        d.min_y = empty_min_y;
        d.max_y = empty_max_y;
        return d;
    }

    if((max_y - min_y) < 1e-9f) {
        min_y -= 0.5f;
        max_y += 0.5f;
    }
    else {
        float y_pad = (max_y - min_y) * 0.1f;
        min_y -= y_pad;
        max_y += y_pad;
    }

    d.min_y = min_y;
    d.max_y = max_y;
    return d;
}
