#include "qvgl/qvgl_runtime.h"

void qvgl_runtime_init(void)
{
}

float qvgl_map_linear_f32(float v, float in_min, float in_max, float out_min, float out_max)
{
    if(in_max == in_min) return out_min;
    float t = (v - in_min) / (in_max - in_min);
    return out_min + t * (out_max - out_min);
}
