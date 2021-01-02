cmake_minimum_required(VERSION 3.10)
project(compile-time-print-tool CXX)

add_compile_options(
        -std=c++17
        -Wall
        -Wextra
        -Wconversion
)

add_library(${PROJECT_NAME} INTERFACE)

target_include_directories(${PROJECT_NAME} INTERFACE
        include/
        )

add_subdirectory(tests/data)
