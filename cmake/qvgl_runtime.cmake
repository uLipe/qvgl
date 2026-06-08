# Generic CMake helper — include from any host or cross CMake project (not ESP-IDF specific).
#
#   set(QVGL_ROOT /path/to/qvgl)
#   set(QVGL_LVGL_PATH /path/to/lvgl)
#   include(${QVGL_ROOT}/cmake/qvgl_runtime.cmake)
#   qvgl_add_runtime_libraries()
#   target_link_libraries(my_app PRIVATE qvgl_runtime_lvgl)

cmake_minimum_required(VERSION 3.16)

function(qvgl_add_runtime_libraries)
    if(NOT QVGL_ROOT)
        message(FATAL_ERROR "QVGL_ROOT must be set before qvgl_add_runtime_libraries()")
    endif()
    if(NOT TARGET qvgl_runtime)
        add_library(qvgl_runtime STATIC
            "${QVGL_ROOT}/runtime/qvgl_runtime.c"
            "${QVGL_ROOT}/runtime/qvgl_plot.c"
        )
        target_include_directories(qvgl_runtime PUBLIC "${QVGL_ROOT}/include")
    endif()
    if(NOT TARGET qvgl_runtime_lvgl)
        if(NOT QVGL_LVGL_PATH OR NOT IS_DIRECTORY "${QVGL_LVGL_PATH}")
            message(FATAL_ERROR "QVGL_LVGL_PATH required for qvgl_runtime_lvgl")
        endif()
        add_library(qvgl_runtime_lvgl STATIC
            "${QVGL_ROOT}/runtime/qvgl_plot_lvgl.c"
            "${QVGL_ROOT}/runtime/qvgl_widget.c"
        )
        target_include_directories(qvgl_runtime_lvgl PUBLIC
            "${QVGL_ROOT}/include"
            "${QVGL_LVGL_PATH}"
        )
        if(QVGL_LV_CONF_DIR)
            target_include_directories(qvgl_runtime_lvgl PUBLIC "${QVGL_LV_CONF_DIR}")
            target_compile_definitions(qvgl_runtime_lvgl PUBLIC LV_CONF_INCLUDE_SIMPLE)
        endif()
        target_link_libraries(qvgl_runtime_lvgl PUBLIC qvgl_runtime)
    endif()
endfunction()
