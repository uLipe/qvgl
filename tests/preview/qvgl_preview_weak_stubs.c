#include "qvgl/qvgl_plot.h"

struct qvgl_preview_ui_opaque;
typedef struct qvgl_preview_ui_opaque qvgl_preview_ui_t;

__attribute__((weak)) void qvgl_preview_set_plot_points(
    qvgl_preview_ui_t * ui, const qvgl_plot_point_t * pts, size_t count)
{
    (void)ui;
    (void)pts;
    (void)count;
}
