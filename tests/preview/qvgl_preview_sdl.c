#include "qvgl_preview_sdl.h"

#if QVGL_PREVIEW_HAVE_SDL

#include <SDL.h>
#include <stdlib.h>
#include <string.h>

struct qvgl_preview_sdl {
    SDL_Window * window;
    SDL_Renderer * renderer;
    SDL_Texture * texture;
    int32_t w;
    int32_t h;
};

static void xrgb_to_rgb565_le(const uint8_t * xrgb, uint16_t * out, size_t count)
{
    for(size_t i = 0; i < count; i++) {
        uint8_t r = xrgb[i * 4 + 0];
        uint8_t g = xrgb[i * 4 + 1];
        uint8_t b = xrgb[i * 4 + 2];
        out[i] = (uint16_t)(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3));
    }
}

qvgl_preview_sdl_t * qvgl_preview_sdl_create(int32_t w, int32_t h, const char * title)
{
    if(SDL_Init(SDL_INIT_VIDEO) != 0) return NULL;

    qvgl_preview_sdl_t * ctx = calloc(1, sizeof(*ctx));
    if(!ctx) return NULL;

    ctx->w = w;
    ctx->h = h;
    ctx->window = SDL_CreateWindow(title ? title : "qvgl_preview", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, w, h,
                                   SDL_WINDOW_SHOWN);
    if(!ctx->window) goto fail;

    ctx->renderer = SDL_CreateRenderer(ctx->window, -1, SDL_RENDERER_SOFTWARE);
    if(!ctx->renderer) goto fail;

    ctx->texture = SDL_CreateTexture(ctx->renderer, SDL_PIXELFORMAT_RGB565, SDL_TEXTUREACCESS_STREAMING, w, h);
    if(!ctx->texture) goto fail;

    return ctx;

fail:
    qvgl_preview_sdl_destroy(ctx);
    return NULL;
}

void qvgl_preview_sdl_destroy(qvgl_preview_sdl_t * ctx)
{
    if(!ctx) return;
    if(ctx->texture) SDL_DestroyTexture(ctx->texture);
    if(ctx->renderer) SDL_DestroyRenderer(ctx->renderer);
    if(ctx->window) SDL_DestroyWindow(ctx->window);
    free(ctx);
    SDL_Quit();
}

bool qvgl_preview_sdl_present(qvgl_preview_sdl_t * ctx, const lv_draw_buf_t * draw_buf)
{
    if(!ctx || !draw_buf) return false;

    uint32_t w = draw_buf->header.w;
    uint32_t h = draw_buf->header.h;
    const uint8_t * src = draw_buf->data;
    uint32_t stride = draw_buf->header.stride;

    void * pixels = NULL;
    int pitch = 0;
    if(SDL_LockTexture(ctx->texture, NULL, &pixels, &pitch) != 0) return false;

    for(uint32_t y = 0; y < h; y++) {
        const uint8_t * row = src + y * stride;
        xrgb_to_rgb565_le(row, (uint16_t *)((uint8_t *)pixels + y * pitch), w);
    }

    SDL_UnlockTexture(ctx->texture);
    SDL_RenderClear(ctx->renderer);
    SDL_RenderCopy(ctx->renderer, ctx->texture, NULL, NULL);
    SDL_RenderPresent(ctx->renderer);
    return true;
}

void qvgl_preview_sdl_poll(void)
{
    SDL_Event ev;
    while(SDL_PollEvent(&ev)) {
        if(ev.type == SDL_QUIT) exit(0);
    }
}

#else

qvgl_preview_sdl_t * qvgl_preview_sdl_create(int32_t w, int32_t h, const char * title)
{
    LV_UNUSED(w);
    LV_UNUSED(h);
    LV_UNUSED(title);
    return NULL;
}

void qvgl_preview_sdl_destroy(qvgl_preview_sdl_t * ctx)
{
    LV_UNUSED(ctx);
}

bool qvgl_preview_sdl_present(qvgl_preview_sdl_t * ctx, const lv_draw_buf_t * draw_buf)
{
    LV_UNUSED(ctx);
    LV_UNUSED(draw_buf);
    return false;
}

void qvgl_preview_sdl_poll(void)
{
}

#endif
