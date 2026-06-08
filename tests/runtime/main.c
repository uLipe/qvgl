#include "qvgl_test.h"
#include "qvgl/ir_v1.h"
#include "qvgl/qvgl_plot.h"
#include "qvgl/qvgl_runtime.h"

#include <string.h>

static void test_ir_header_constants(void)
{
    QVGL_ASSERT(QVGLIR_MAGIC == 0x31564751u);
    QVGL_ASSERT(QVGLIR_VERSION == 1u);
}

static void test_runtime_map_linear(void)
{
    float v_min = qvgl_map_linear_f32(-0.7f, -0.7f, 2.0f, 210.0f, -30.0f);
    float v_mid = qvgl_map_linear_f32(0.0f, -0.7f, 2.0f, 210.0f, -30.0f);
    QVGL_ASSERT(v_min > 209.0f && v_min < 211.0f);
    QVGL_ASSERT(v_mid > 140.0f && v_mid < 155.0f);
}

static void test_plot_format_axis(void)
{
    char buf[24];
    qvgl_plot_format_axis(1.3f, buf, sizeof(buf));
    QVGL_ASSERT(strcmp(buf, "1.30") == 0);
    qvgl_plot_format_axis(0.7f, buf, sizeof(buf));
    QVGL_ASSERT(strcmp(buf, "0.700") == 0);
}

static void test_plot_compute_domain(void)
{
    const qvgl_plot_point_t pts[] = {
        {0.0f, 0.2f}, {2.5f, -0.9f}, {5.0f, -0.2f},
    };
    qvgl_plot_domain_t d = qvgl_plot_compute_domain(pts, 3, 0.0f, 5.0f, -1.0f, 1.0f);
    QVGL_ASSERT(d.min_x == 0.0f);
    QVGL_ASSERT(d.max_x == 5.0f);
    QVGL_ASSERT(d.min_y < -0.9f);
    QVGL_ASSERT(d.max_y > 0.2f);
}

int main(void)
{
    QVGL_TEST_RUN(test_ir_header_constants);
    QVGL_TEST_RUN(test_runtime_map_linear);
    QVGL_TEST_RUN(test_plot_format_axis);
    QVGL_TEST_RUN(test_plot_compute_domain);
    return EXIT_SUCCESS;
}
