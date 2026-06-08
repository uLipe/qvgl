add_executable(qvgl_runtime_unit main.c)
target_include_directories(qvgl_runtime_unit PRIVATE ${CMAKE_SOURCE_DIR}/include ${CMAKE_SOURCE_DIR}/tests/harness)
target_link_libraries(qvgl_runtime_unit PRIVATE qvgl_runtime m)
add_test(NAME runtime_unit COMMAND qvgl_runtime_unit)
