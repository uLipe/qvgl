add_library(qvgl_runtime STATIC qvgl_runtime.c qvgl_vehicle_model.c)
target_include_directories(qvgl_runtime PUBLIC ${CMAKE_SOURCE_DIR}/include)
