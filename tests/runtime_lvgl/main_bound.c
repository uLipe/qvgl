#include "qvgl_preview_display.h"
#include "qvgl_test.h"

#include "lvgl.h"

void test_bound_setters_title(void);

int main(void)
{
    lv_init();
    lv_display_t * disp = qvgl_preview_display_create(320, 240);
    if(!disp) return EXIT_FAILURE;
    lv_display_set_default(disp);

    QVGL_TEST_RUN(test_bound_setters_title);

    lv_display_delete(disp);
    lv_deinit();
    return EXIT_SUCCESS;
}
