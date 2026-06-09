if(NOT TARGET lvgl)
    message(WARNING "lvgl target missing; skipping qvgl_runtime_lvgl")
    return()
endif()

find_package(Python3 COMPONENTS Interpreter REQUIRED)

set(BOUND_FIXTURE_DIR "${CMAKE_BINARY_DIR}/qvgl_fixtures/bound_props_card")
set(BOUND_UI_C "${BOUND_FIXTURE_DIR}/ui_bound_props_card.c")

add_custom_command(
    OUTPUT ${BOUND_UI_C}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${BOUND_FIXTURE_DIR}
    COMMAND ${CMAKE_COMMAND} -E env PYTHONPATH=${CMAKE_SOURCE_DIR}
        ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/qvglc/cli.py compile
        ${CMAKE_SOURCE_DIR}/examples/bound_props_card/bound_props_card.qml
        -o ${BOUND_FIXTURE_DIR}
        --lvgl-path ${QVGL_LVGL_PATH}
        --profile ${CMAKE_SOURCE_DIR}/profiles/ultralite_v1.yaml
    DEPENDS
        ${CMAKE_SOURCE_DIR}/examples/bound_props_card/bound_props_card.qml
        ${CMAKE_SOURCE_DIR}/profiles/ultralite_v1.yaml
    COMMENT "Generating bound_props_card LVGL fixture"
    VERBATIM
)

add_executable(qvgl_runtime_lvgl_test
    main.c
    test_widget.c
    test_controls.c
    test_plot.c
    test_bound_setters.c
    ${CMAKE_SOURCE_DIR}/tests/preview/qvgl_preview_display.c
    ${BOUND_UI_C}
)
target_include_directories(qvgl_runtime_lvgl_test PRIVATE
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/tests/harness
    ${CMAKE_SOURCE_DIR}/tests/preview
    ${BOUND_FIXTURE_DIR}
    "${QVGL_LVGL_PATH}"
)
target_link_libraries(qvgl_runtime_lvgl_test PRIVATE lvgl qvgl_runtime_lvgl qvgl_runtime m)
add_test(NAME runtime_lvgl COMMAND qvgl_runtime_lvgl_test)
