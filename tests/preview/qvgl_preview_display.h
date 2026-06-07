#ifndef QVGL_PREVIEW_DISPLAY_H
#define QVGL_PREVIEW_DISPLAY_H

#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

lv_display_t * qvgl_preview_display_create(int32_t hor_res, int32_t ver_res);

const lv_draw_buf_t * qvgl_preview_display_draw_buf(lv_display_t * disp);

#ifdef __cplusplus
}
#endif

#endif
