function(create_example name)
    add_library(${name}
            ${name}
            )

    target_compile_options(${name} PRIVATE
            -fpermissive
            )

    target_link_libraries(${name} PRIVATE
            ${PROJECT_NAME}
            )
endfunction()

create_example(example.cpp)
create_example(fibonacci.cpp)
create_example(fibonacci_with_noise.cpp)
create_example(no_print_statement.cpp)
create_example(output_stream.cpp)
create_example(type_stack.cpp)
create_example(user_defined_type.cpp)
create_example(value_stack.cpp)
create_example(workarounds.cpp)
