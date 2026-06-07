#include "qvgl_test.h"
#include "qvgl/ir_v1.h"
#include "qvgl/qvgl_runtime.h"
#include "qvgl/qvgl_vehicle_model.h"

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

static void test_vehicle_demo_can_decode(void)
{
    qvgl_vehicle_state_t st;
    qvgl_vehicle_state_init(&st);
    const uint8_t frame[] = {0xB0u, 0x04u, 0xACu, 0x0Du, 0x03u, 0x00u};
    QVGL_ASSERT(qvgl_vehicle_decode_demo_can(QVGL_VEHICLE_DEMO_CAN_SPEED_RPM, frame, 6, &st));
    QVGL_ASSERT(st.speed_kmh > 119.9f && st.speed_kmh < 120.1f);
    QVGL_ASSERT(st.rpm > 3509.0f && st.rpm < 3511.0f);
    QVGL_ASSERT(st.gear == 3u);
}

int main(void)
{
    QVGL_TEST_RUN(test_ir_header_constants);
    QVGL_TEST_RUN(test_runtime_map_linear);
    QVGL_TEST_RUN(test_vehicle_demo_can_decode);
    return EXIT_SUCCESS;
}
