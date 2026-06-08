#include "qvgl_test.h"
#include "qvgl/ir_v1.h"
#include "qvgl/qvgl_runtime.h"

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

int main(void)
{
    QVGL_TEST_RUN(test_ir_header_constants);
    QVGL_TEST_RUN(test_runtime_map_linear);
    return EXIT_SUCCESS;
}
