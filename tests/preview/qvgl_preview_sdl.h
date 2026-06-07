#ifndef QVGL_PREVIEW_SDL_H
#define QVGL_PREVIEW_SDL_H

#include "lvgl.h"

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct qvgl_preview_sdl qvgl_preview_sdl_t;

qvgl_preview_sdl_t * qvgl_preview_sdl_create(int32_t w, int32_t h, const char * title);
void qvgl_preview_sdl_destroy(qvgl_preview_sdl_t * ctx);
bool qvgl_preview_sdl_present(qvgl_preview_sdl_t * ctx, const lv_draw_buf_t * draw_buf);
void qvgl_preview_sdl_poll(void);

#ifdef __cplusplus
}
#endif

#endif
