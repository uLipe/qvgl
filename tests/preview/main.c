#include "qvgl_preview_display.h"
#include "qvgl_preview_png.h"
#include "qvgl_preview_sdl.h"
#include "qvgl_preview_shim.h"
#include "qvgl/qvgl_plot.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define QVGL_MAX_OVERRIDES 16

static uint32_t s_tick_ms;

static uint32_t tick_get(void)
{
    return s_tick_ms;
}

static void tick_inc(uint32_t ms)
{
    s_tick_ms += ms;
}

void app_on_gauge_clicked(void)
{
    fprintf(stderr, "qvgl_preview: gauge clicked\n");
}

void app_on_plot_close(void)
{
}

void app_on_gain_moved(void)
{
}

void app_on_output_toggled(void)
{
}

void app_on_mute_toggled(void)
{
}

void app_on_gain_changed(void)
{
}

void app_on_preset_activated(void)
{
}

void app_on_apply_clicked(void)
{
}

void app_on_dim_moved(void)
{
}

void app_on_panel_toggled(void)
{
}

void app_on_enable_pressed(void)
{
}

void app_on_enable_released(void)
{
}

void app_on_action_clicked(void)
{
}

void app_on_eco_selected(void)
{
}

void app_on_sport_selected(void)
{
}

typedef struct {
    char name[64];
    char value[128];
} prop_override_t;

typedef struct {
    const char * gen_dir;
    bool headless;
    bool pressure_provided;
    float pressure;
    prop_override_t overrides[QVGL_MAX_OVERRIDES];
    int override_count;
    uint32_t frames;
    uint32_t loop_frames;
    const char * dump_fb;
    bool exit_after;
    bool plot_cursor_set;
    float plot_t;
    float plot_y;
    bool plot_animate;
} preview_opts_t;

static void usage(const char * argv0)
{
    fprintf(stderr,
            "Usage: %s --gen-dir DIR [options]\n"
            "  --headless           no SDL window\n"
            "  --set NAME=VALUE     module property override (repeatable; typed)\n"
            "  --pressure FLOAT     alias for --set pressure=FLOAT (legacy)\n"
            "  --frames N           refr frames before dump (default 3)\n"
            "  --plot-cursor T,Y    show plot crosshair at data coords (repeatable)\n"
            "  --plot-animate       feed synthetic sine series each loop frame\n"
            "  --dump-fb PATH       write PNG of LVGL draw buffer\n"
            "  --loop-frames N      interactive/dummy loop iterations (default 0)\n"
            "  --exit               exit after loop (for CI smoke)\n",
            argv0);
}

static int add_override(preview_opts_t * o, const char * name, const char * value)
{
    if(o->override_count >= QVGL_MAX_OVERRIDES) {
        fprintf(stderr, "qvgl_preview: too many --set overrides\n");
        return -1;
    }
    prop_override_t * slot = &o->overrides[o->override_count++];
    strncpy(slot->name, name, sizeof(slot->name) - 1);
    slot->name[sizeof(slot->name) - 1] = '\0';
    strncpy(slot->value, value, sizeof(slot->value) - 1);
    slot->value[sizeof(slot->value) - 1] = '\0';
    return 0;
}

static int parse_set_arg(preview_opts_t * o, const char * arg)
{
    const char * eq = strchr(arg, '=');
    if(!eq || eq == arg) {
        fprintf(stderr, "qvgl_preview: invalid --set %s (expected NAME=VALUE)\n", arg);
        return -1;
    }
    char name[64];
    size_t nlen = (size_t)(eq - arg);
    if(nlen >= sizeof(name)) {
        fprintf(stderr, "qvgl_preview: property name too long in --set %s\n", arg);
        return -1;
    }
    memcpy(name, arg, nlen);
    name[nlen] = '\0';
    return add_override(o, name, eq + 1);
}

static int parse_args(int argc, char ** argv, preview_opts_t * o)
{
    memset(o, 0, sizeof(*o));
    o->pressure = -0.7f;
    o->frames = 3;

    for(int i = 1; i < argc; i++) {
        if(strcmp(argv[i], "--gen-dir") == 0 && i + 1 < argc) {
            o->gen_dir = argv[++i];
        }
        else if(strcmp(argv[i], "--headless") == 0) {
            o->headless = true;
        }
        else if(strcmp(argv[i], "--pressure") == 0 && i + 1 < argc) {
            o->pressure = (float)strtod(argv[++i], NULL);
            o->pressure_provided = true;
        }
        else if(strcmp(argv[i], "--set") == 0 && i + 1 < argc) {
            if(parse_set_arg(o, argv[++i]) != 0) return -1;
        }
        else if(strcmp(argv[i], "--frames") == 0 && i + 1 < argc) {
            o->frames = (uint32_t)strtoul(argv[++i], NULL, 10);
        }
        else if(strcmp(argv[i], "--plot-cursor") == 0 && i + 1 < argc) {
            const char * arg = argv[++i];
            const char * comma = strchr(arg, ',');
            if(!comma) {
                fprintf(stderr, "qvgl_preview: invalid --plot-cursor %s (expected T,Y)\n", arg);
                return -1;
            }
            char tbuf[32];
            size_t tlen = (size_t)(comma - arg);
            if(tlen >= sizeof(tbuf)) {
                fprintf(stderr, "qvgl_preview: plot cursor t too long\n");
                return -1;
            }
            memcpy(tbuf, arg, tlen);
            tbuf[tlen] = '\0';
            o->plot_t = (float)strtod(tbuf, NULL);
            o->plot_y = (float)strtod(comma + 1, NULL);
            o->plot_cursor_set = true;
        }
        else if(strcmp(argv[i], "--dump-fb") == 0 && i + 1 < argc) {
            o->dump_fb = argv[++i];
        }
        else if(strcmp(argv[i], "--loop-frames") == 0 && i + 1 < argc) {
            o->loop_frames = (uint32_t)strtoul(argv[++i], NULL, 10);
        }
        else if(strcmp(argv[i], "--exit") == 0) {
            o->exit_after = true;
        }
        else if(strcmp(argv[i], "--plot-animate") == 0) {
            o->plot_animate = true;
        }
        else {
            usage(argv[0]);
            return -1;
        }
    }

    if(!o->gen_dir) {
        usage(argv[0]);
        return -1;
    }

    if(o->pressure_provided) {
        char pbuf[32];
        snprintf(pbuf, sizeof(pbuf), "%g", (double)o->pressure);
        if(add_override(o, "pressure", pbuf) != 0) return -1;
    }
    return 0;
}

static void apply_overrides(qvgl_preview_ui_t * ui, const preview_opts_t * o)
{
    for(int i = 0; i < o->override_count; i++) {
        const prop_override_t * ov = &o->overrides[i];
        if(qvgl_preview_apply_property(ui, ov->name, ov->value) != 0) {
            float f = (float)strtod(ov->value, NULL);
            if(qvgl_preview_set_property(ui, ov->name, f) != 0) {
                fprintf(stderr, "qvgl_preview: unknown property %s\n", ov->name);
            }
        }
    }
}

static void pump_lvgl(uint32_t frames)
{
    for(uint32_t i = 0; i < frames; i++) {
        tick_inc(5);
        lv_tick_inc(5);
        lv_timer_handler();
    }
}

int main(int argc, char ** argv)
{
    preview_opts_t opts;
    if(parse_args(argc, argv, &opts) != 0) return 1;

    LV_UNUSED(opts.gen_dir);

    lv_init();
    lv_tick_set_cb(tick_get);

    const int32_t w = qvgl_preview_width();
    const int32_t h = qvgl_preview_height();
    lv_display_t * disp = qvgl_preview_display_create(w, h);
    if(!disp) {
        fprintf(stderr, "qvgl_preview: display create failed\n");
        return 1;
    }

    lv_display_set_default(disp);

    qvgl_preview_ui_t ui;
    qvgl_preview_ui_create(lv_screen_active(), &ui);
    qvgl_preview_ui_sync(&ui);
    apply_overrides(&ui, &opts);
    if(opts.plot_cursor_set) {
        qvgl_preview_set_plot_cursor(&ui, opts.plot_t, opts.plot_y);
    }

    lv_obj_invalidate(lv_screen_active());
    pump_lvgl(opts.frames);
    lv_refr_now(disp);

    if(opts.dump_fb) {
        const lv_draw_buf_t * buf = qvgl_preview_display_draw_buf(disp);
        if(!buf || buf->header.w == 0 || buf->header.h == 0) {
            fprintf(stderr, "qvgl_preview: invalid draw buffer\n");
            return 1;
        }
        if(qvgl_preview_png_write_draw_buf(buf, opts.dump_fb) != 0) {
            fprintf(stderr, "qvgl_preview: PNG write failed: %s\n", opts.dump_fb);
            return 1;
        }
    }

    qvgl_preview_sdl_t * sdl = NULL;
    if(!opts.headless) {
        sdl = qvgl_preview_sdl_create(w, h, qvgl_preview_title());
        if(sdl) qvgl_preview_sdl_present(sdl, qvgl_preview_display_draw_buf(disp));
    }

    if(opts.loop_frames > 0 || sdl) {
        uint32_t n = opts.loop_frames > 0 ? opts.loop_frames : 600;
        for(uint32_t i = 0; i < n; i++) {
            if(opts.plot_animate) {
                qvgl_plot_point_t pts[32];
                for(int k = 0; k < 32; k++) {
                    float t = (float)k / 31.0f * 5.0f;
                    pts[k].x = t;
                    pts[k].y = sinf(t * 1.2f + (float)i * 0.15f) * 0.85f;
                }
                qvgl_preview_set_plot_points(&ui, pts, 32);
                lv_obj_invalidate(lv_screen_active());
            }
            pump_lvgl(1);
            if(sdl) {
                qvgl_preview_sdl_present(sdl, qvgl_preview_display_draw_buf(disp));
                qvgl_preview_sdl_poll();
            }
            if(opts.exit_after && i + 1 >= opts.loop_frames) break;
        }
    }

    qvgl_preview_sdl_destroy(sdl);
    return 0;
}
