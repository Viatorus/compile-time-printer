cmake_minimum_required(VERSION 3.10)
project(example CXX)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(${PROJECT_NAME} example.cpp)
target_link_libraries(${PROJECT_NAME} ${CONAN_LIBS})

set_target_properties(${PROJECT_NAME} PROPERTIES
        CXX_STANDARD 17
        CXX_STANDARD_REQUIRED ON
        )
