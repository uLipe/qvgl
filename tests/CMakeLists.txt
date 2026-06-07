add_executable(qvgl_tests harness/smoke.c)
target_include_directories(qvgl_tests PRIVATE ${CMAKE_SOURCE_DIR}/include ${CMAKE_SOURCE_DIR}/tests/harness)
target_link_libraries(qvgl_tests PRIVATE qvgl_runtime)
add_test(NAME smoke COMMAND qvgl_tests)
