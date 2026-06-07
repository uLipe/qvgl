#ifndef LV_CONF_H
#define LV_CONF_H

#define LV_CONF_SUPPRESS_DEFINE_CHECK 1

#include <stddef.h>
#include <stdint.h>

#define LV_COLOR_DEPTH              32
#define LV_USE_STDLIB_MALLOC        LV_STDLIB_CLIB
#define LV_USE_STDLIB_STRING        LV_STDLIB_CLIB
#define LV_USE_STDLIB_SPRINTF       LV_STDLIB_CLIB
#define LV_USE_OS                   LV_OS_NONE

#define LV_MEM_SIZE                 (8 * 1024 * 1024)
#define LV_DEF_REFR_PERIOD          33

#define LV_USE_LOG                  0
#define LV_USE_ASSERT_NULL          1
#define LV_USE_ASSERT_MALLOC        1
#define LV_USE_ASSERT_OBJ           0
#define LV_USE_ASSERT_STYLE         0

#define LV_USE_ARC                  1
#define LV_USE_SCALE                1
#define LV_USE_ANIM                 1
#define LV_USE_LABEL                1
#define LV_USE_IMAGE                1
#define LV_USE_LODEPNG              1

#define LV_FONT_MONTSERRAT_14       1
#define LV_FONT_MONTSERRAT_36       1
#define LV_FONT_MONTSERRAT_48       1
#define LV_FONT_DEFAULT             &lv_font_montserrat_14

#define LV_USE_THEME_DEFAULT        1

#define LV_USE_FS_STDIO             1
#define LV_FS_STDIO_LETTER          'A'
#define LV_FS_STDIO_PATH            ""
#define LV_FS_DEFAULT_DRIVER_LETTER 'A'

#endif /* LV_CONF_H */
