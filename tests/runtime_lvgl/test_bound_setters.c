#include "qvgl/qvgl_widget.h"
#include "qvgl_bound_props_card.h"
#include "qvgl_test.h"
#include "ui_bound_props_card.h"

#include <string.h>

void test_bound_setters_title(void)
{
    qvgl_ui_bound_props_card_t ui = {0};
    qvgl_ui_bound_props_card_create(lv_screen_active(), &ui);
    qvgl_bound_props_card_set_title(&ui, "Ib");
    QVGL_ASSERT(strcmp(lv_label_get_text(ui.title_label), "Ib") == 0);
    qvgl_bound_props_card_set_alarm(&ui, true);
    QVGL_ASSERT(!lv_obj_has_flag(ui.alarm_bar, LV_OBJ_FLAG_HIDDEN));
}
