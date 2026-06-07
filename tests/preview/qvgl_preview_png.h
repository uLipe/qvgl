#ifndef QVGL_PREVIEW_PNG_H
#define QVGL_PREVIEW_PNG_H

#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

int qvgl_preview_png_write_draw_buf(const lv_draw_buf_t * draw_buf, const char * path);

#ifdef __cplusplus
}
#endif

#endif
