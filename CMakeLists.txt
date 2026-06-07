cmake_minimum_required(VERSION 3.16)
project(qvgl LANGUAGES C CXX)

option(QVGL_BUILD_TESTS "Build C runtime test suite" ON)
option(QVGL_BUILD_PREVIEW "Build SDL preview harness" OFF)

set(QVGL_LVGL_PATH "" CACHE PATH "LVGL tree for emit probe and preview")

add_subdirectory(runtime)

if(QVGL_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

if(QVGL_BUILD_PREVIEW OR QVGL_BUILD_TESTS)
    if(NOT QVGL_LVGL_PATH)
        set(QVGL_LVGL_PATH "${CMAKE_SOURCE_DIR}/../lvgl" CACHE PATH "LVGL tree for preview")
    endif()
    add_subdirectory(tests/preview)
endif()
