add_subdirectory(runtime)

if(QVGL_LVGL_PATH AND IS_DIRECTORY "${QVGL_LVGL_PATH}" AND NOT TARGET lvgl)
    set(LV_BUILD_CONF_PATH "${CMAKE_SOURCE_DIR}/tests/preview/lv_conf.h" CACHE STRING "qvgl lv_conf" FORCE)
    set(CONFIG_LV_BUILD_DEMOS OFF CACHE BOOL "" FORCE)
    set(CONFIG_LV_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
    set(LV_BUILD_SET_CONFIG_OPTS OFF CACHE BOOL "" FORCE)
    add_subdirectory("${QVGL_LVGL_PATH}" "${CMAKE_BINARY_DIR}/qvgl_lvgl" EXCLUDE_FROM_ALL)
endif()

add_subdirectory(runtime_lvgl)
