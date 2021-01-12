cmake_minimum_required(VERSION 3.10)
project(compile-time-print-tool CXX)

add_library(${PROJECT_NAME} INTERFACE)

target_compile_features(${PROJECT_NAME} INTERFACE cxx_std_17)

target_compile_options(${PROJECT_NAME} INTERFACE
        -Wall
        -Wextra
        -Wconversion)

target_include_directories(${PROJECT_NAME} INTERFACE
        include/
        )

add_subdirectory(tests/data)
