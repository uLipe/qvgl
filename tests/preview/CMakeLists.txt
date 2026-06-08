if(NOT QVGL_LVGL_PATH OR NOT IS_DIRECTORY "${QVGL_LVGL_PATH}")
    message(WARNING "QVGL_LVGL_PATH not set; skipping qvgl_preview")
    return()
endif()

if(NOT TARGET lvgl)
    message(WARNING "lvgl target missing; skipping qvgl_preview")
    return()
endif()

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
    qvgl_preview_weak_stubs.c
    ${QVGL_PREVIEW_GEN_SOURCES}
)

target_include_directories(qvgl_preview PRIVATE
    "${QVGL_PREVIEW_GEN_DIR}"
    "${QVGL_LVGL_PATH}/src"
    "${CMAKE_SOURCE_DIR}/include"
)

target_link_libraries(qvgl_preview PRIVATE lvgl qvgl_runtime_lvgl qvgl_runtime m)

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
