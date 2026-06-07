#include "qvgl_preview_display.h"

#include <stdlib.h>

typedef struct {
    lv_draw_buf_t draw_buf;
    uint8_t * unaligned;
} qvgl_preview_display_ctx_t;

static void flush_cb(lv_display_t * disp, const lv_area_t * area, uint8_t * color_p);
static void delete_cb(lv_event_t * e);

lv_display_t * qvgl_preview_display_create(int32_t hor_res, int32_t ver_res)
{
    lv_display_t * disp = lv_display_create(hor_res, ver_res);
    if(!disp) return NULL;

    lv_display_set_color_format(disp, LV_COLOR_FORMAT_XRGB8888);

    qvgl_preview_display_ctx_t * ctx = lv_malloc_zeroed(sizeof(*ctx));
    if(!ctx) {
        lv_display_delete(disp);
        return NULL;
    }

    size_t buf_size = 4 * (size_t)(hor_res + LV_DRAW_BUF_STRIDE_ALIGN - 1) * (size_t)ver_res + LV_DRAW_BUF_ALIGN;
    ctx->unaligned = malloc(buf_size);
    if(!ctx->unaligned) {
        lv_free(ctx);
        lv_display_delete(disp);
        return NULL;
    }

    lv_draw_buf_init(&ctx->draw_buf, hor_res, ver_res, LV_COLOR_FORMAT_XRGB8888, LV_STRIDE_AUTO,
                     lv_draw_buf_align(ctx->unaligned, LV_COLOR_FORMAT_XRGB8888), buf_size);
    ctx->draw_buf.unaligned_data = ctx->unaligned;

    lv_display_set_driver_data(disp, ctx);
    lv_display_set_draw_buffers(disp, &ctx->draw_buf, NULL);
    lv_display_set_render_mode(disp, LV_DISPLAY_RENDER_MODE_DIRECT);
    lv_display_set_flush_cb(disp, flush_cb);
    lv_display_add_event_cb(disp, delete_cb, LV_EVENT_DELETE, NULL);

    return disp;
}

const lv_draw_buf_t * qvgl_preview_display_draw_buf(lv_display_t * disp)
{
    return lv_display_get_buf_active(disp);
}

static void flush_cb(lv_display_t * disp, const lv_area_t * area, uint8_t * color_p)
{
    LV_UNUSED(area);
    LV_UNUSED(color_p);
    lv_display_flush_ready(disp);
}

static void delete_cb(lv_event_t * e)
{
    lv_display_t * disp = lv_event_get_target(e);
    qvgl_preview_display_ctx_t * ctx = lv_display_get_driver_data(disp);
    if(!ctx) return;
    free(ctx->unaligned);
    lv_free(ctx);
}
