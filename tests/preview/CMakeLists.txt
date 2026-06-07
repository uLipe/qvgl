if(NOT QVGL_LVGL_PATH OR NOT IS_DIRECTORY "${QVGL_LVGL_PATH}")
    message(WARNING "QVGL_LVGL_PATH not set; skipping qvgl_preview")
    return()
endif()

set(LV_BUILD_CONF_PATH "${CMAKE_CURRENT_SOURCE_DIR}/lv_conf.h" CACHE STRING "qvgl preview lv_conf" FORCE)
set(CONFIG_LV_BUILD_DEMOS OFF CACHE BOOL "" FORCE)
set(CONFIG_LV_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(LV_BUILD_SET_CONFIG_OPTS OFF CACHE BOOL "" FORCE)

add_subdirectory("${QVGL_LVGL_PATH}" "${CMAKE_BINARY_DIR}/lvgl_preview_lvgl" EXCLUDE_FROM_ALL)

set(QVGL_PREVIEW_GEN_DIR "" CACHE PATH "Generated UI directory (ui_*.c from qvglc compile)")

file(GLOB QVGL_PREVIEW_GEN_SOURCES "${QVGL_PREVIEW_GEN_DIR}/*.c")
if(NOT QVGL_PREVIEW_GEN_SOURCES)
    message(WARNING "QVGL_PREVIEW_GEN_DIR has no ui_*.c — run qvglc compile first")
    return()
endif()

find_package(SDL2 QUIET)

add_executable(qvgl_preview
    main.c
    qvgl_preview_display.c
    qvgl_preview_png.c
    qvgl_preview_sdl.c
    ${QVGL_PREVIEW_GEN_SOURCES}
)

target_include_directories(qvgl_preview PRIVATE
    "${QVGL_PREVIEW_GEN_DIR}"
    "${QVGL_LVGL_PATH}/src"
)

target_link_libraries(qvgl_preview PRIVATE lvgl m)

if(SDL2_FOUND)
    target_compile_definitions(qvgl_preview PRIVATE QVGL_PREVIEW_HAVE_SDL=1)
    target_link_libraries(qvgl_preview PRIVATE SDL2::SDL2)
else()
    target_compile_definitions(qvgl_preview PRIVATE QVGL_PREVIEW_HAVE_SDL=0)
endif()

if(QVGL_BUILD_TESTS)
    add_test(
        NAME preview_headless_dump
        COMMAND qvgl_preview
            --gen-dir "${QVGL_PREVIEW_GEN_DIR}"
            --headless
            --pressure -0.7
            --frames 5
            --dump-fb "${CMAKE_BINARY_DIR}/preview_p-0.7.png"
    )
endif()
