#include "qvgl_preview_png.h"

#include "libs/lodepng/lodepng.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void draw_buf_to_xrgb8888(const lv_draw_buf_t * draw_buf, uint8_t * out)
{
    uint32_t w = draw_buf->header.w;
    uint32_t h = draw_buf->header.h;
    lv_color_format_t cf = draw_buf->header.cf;
    const uint8_t * in = draw_buf->data;
    uint32_t stride = draw_buf->header.stride;

    if(cf == LV_COLOR_FORMAT_XRGB8888 || cf == LV_COLOR_FORMAT_ARGB8888) {
        for(uint32_t y = 0; y < h; y++) {
            const uint8_t * row = in + y * stride;
            uint8_t * dst = out + y * w * 4;
            for(uint32_t x = 0; x < w; x++) {
                dst[x * 4 + 0] = row[x * 4 + 0];
                dst[x * 4 + 1] = row[x * 4 + 1];
                dst[x * 4 + 2] = row[x * 4 + 2];
                dst[x * 4 + 3] = 0xFF;
            }
        }
        return;
    }

    if(cf == LV_COLOR_FORMAT_RGB565) {
        for(uint32_t y = 0; y < h; y++) {
            const uint8_t * row = in + y * stride;
            uint8_t * dst = out + y * w * 4;
            for(uint32_t x = 0; x < w; x++) {
                const lv_color16_t * c16 = (const lv_color16_t *)&row[x * 2];
                dst[x * 4 + 0] = (uint8_t)((c16->blue * 2106) >> 8);
                dst[x * 4 + 1] = (uint8_t)((c16->green * 1037) >> 8);
                dst[x * 4 + 2] = (uint8_t)((c16->red * 2106) >> 8);
                dst[x * 4 + 3] = 0xFF;
            }
        }
    }
}

int qvgl_preview_png_write_draw_buf(const lv_draw_buf_t * draw_buf, const char * path)
{
    if(!draw_buf || !path) return -1;

    uint32_t w = draw_buf->header.w;
    uint32_t h = draw_buf->header.h;
    size_t px_count = (size_t)w * (size_t)h;
    uint8_t * xrgb = lv_malloc(px_count * 4);
    if(!xrgb) return -1;

    draw_buf_to_xrgb8888(draw_buf, xrgb);

    char fs_path[512];
    lv_snprintf(fs_path, sizeof(fs_path), "A:%s", path);

    unsigned err = lodepng_encode32_file(fs_path, xrgb, w, h);
    lv_free(xrgb);
    if(err) {
        fprintf(stderr, "lodepng: %u %s\n", err, lodepng_error_text(err));
        return -2;
    }
    return 0;
}
