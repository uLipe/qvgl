#ifndef QVGL_PLOT_H
#define QVGL_PLOT_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define QVGL_PLOT_SCALE        1000
#define QVGL_PLOT_MAX_TICKS    9
#define QVGL_PLOT_MAX_POINTS   128

typedef struct {
    float x;
    float y;
} qvgl_plot_point_t;

typedef struct {
    float min_x;
    float max_x;
    float min_y;
    float max_y;
} qvgl_plot_domain_t;

int32_t qvgl_plot_scale_f32(float v);

void qvgl_plot_format_axis(float v, char * buf, size_t buf_len);

qvgl_plot_domain_t qvgl_plot_compute_domain(
    const qvgl_plot_point_t * pts,
    size_t count,
    float time_min,
    float time_max,
    float empty_min_y,
    float empty_max_y);

#ifdef __cplusplus
}
#endif

#endif /* QVGL_PLOT_H */
