.. image:: https://raw.githubusercontent.com/Viatorus/compile-time-printer/main/web/static/banner-web.svg
    :alt: compile-time printer

.. image :: https://img.shields.io/github/release/viatorus/compile-time-printer.svg
    :alt: Github Releases
    :target: https://github.com/viatorus/compile-time-printer/releases
.. image :: https://img.shields.io/pypi/v/compile-time-printer.svg
    :alt: PyPI
    :target: https://pypi.org/project/compile-time-printer/
.. image :: https://api.bintray.com/packages/viatorus/compile-time-printer/compile-time-printer%3Aviatorus/images/download.svg
    :alt: Conan
    :target: https://bintray.com/viatorus/compile-time-printer/compile-time-printer%3Aviatorus/_latestVersion
.. image :: https://github.com/Viatorus/compile-time-printer/workflows/Testing/badge.svg
    :alt: Build Status
    :target: https://github.com/viatorus/compile-time-printer/releases
.. image :: https://img.shields.io/badge/try-online-blue.svg
    :alt: Try online
    :target: https://viatorus.github.io/compile-time-printer/

Compile-Time Printer
====================

**Compile-Time Printer** prints values and types at compile-time in C++.

Teaser
------

+-------------------------------------------------+-------------------------------------------------+
|                       test.cpp                  |    ``compile-time-printer -- make test.cpp``    |
+-------------------------------------------------+-------------------------------------------------+
| .. code-block:: cpp                             | .. code-block::                                 |
|                                                 |                                                 |
|     #include <ctp/ctp.hpp>                      |     .                                           |
|                                                 |                                                 |
|     template<auto I>                            |                                                 |
|     constexpr auto func(int i) {                |                                                 |
|                                                 |                                                 |
|       // Formatted output.                      |                                                 |
|       ctp::printf("Hello {}!\n", ctp::type{I}); |     Hello int!                                  |
|                                                 |                                                 |
|       // Standardized output.                   |                                                 |
|       ctp::print(I + i, sizeof(I));             |     42 4                                        |
|                                                 |                                                 |
|       return true;                              |                                                 |
|     }                                           |                                                 |
|                                                 |                                                 |
|     constexpr auto test = func<22>(20);         |                                               . |
+-------------------------------------------------+-------------------------------------------------+

Try it out online: https://viatorus.github.io/compile-time-printer/

Overview
--------

* `Installation`_
* `API`_
* `How it works`_
* `Known limitations`_
* `License`_

Installation
------------

Requires:

* Python >=3.6
* GCC >=7.4 and STD >=C++17

To get started, install the `python tool <https://pypi.org/project/compile-time-printer>`__:

.. code-block::

    pip install compile-time-printer

Afterwards, dump the CTP header file and include it in your project:

.. code-block::

    compile-time-printer --dump-header-file

Alternative, you can install the header file via the
`conan package <https://bintray.com/viatorus/compile-time-printer>`__.

Finally, run CTP with your build command.

*E.g. with g++ directly:*

.. code-block::

    compile-time-printer -- g++ -I. -fsyntax-only -std=c++17 -fpermissive test.cpp

*E.g. with make:*

.. code-block::

    compile-time-printer -- make test.cpp

You have to set the compiler flag *-fpermissive* in order to make it work.

API
---

ctp.hpp
+++++++

* **ctp::print(** *[file descriptor,] arguments* **)**

Prints all arguments in a simple, standardized format. Each argument is separated by one space, ending with a line
break.

.. code-block:: cpp

    int x = 42;
    ctp::print("Hello", 2.72, x);  // "Hello 2.72 42\n"

* **ctp::printf(** *[file descriptor,] format, arguments* **)**

Formats and prints all arguments in the desired format without implicit line break.
Uses the `pythons format string syntax <https://docs.python.org/3/library/string.html#format-string-syntax>`__.

.. code-block:: cpp

    int x = 42;
    ctp::printf("{:.1f}", 3.14);  // "3.1"
    ctp::printf("int: {0:d}; hex: {0:x};\n"    // "int: 42; hex: 2a;\n"
                "oct: {0:o}; bin: {0:b}", x);  // "oct: 52; bin: 101010"

* **ctp::stdout** or **ctp::stderr**

Available file descriptor to print to standard output stream or standard error stream.

.. code-block:: cpp

    ctp::print(ctp::stdout, "Info");  // stdout: "Info\n"
    ctp::printf(ctp::stderr, "Warning!\n");  // stderr: "Warning!\n"

* **ctp::type<** *Types* **>{}** or **ctp::type{** *variables* **}**

Helper object which can be passed as an argument to **print/printf** to output the type of the variables rather then
their values.

.. code-block:: cpp

    int x = 42;
    ctp::print(ctp::type<float>{}, ctp::type{x});  // "float int&\n"

* **ctp::view(** *data begin, data end* **)** or **ctp::view(** *data begin, data length* **)**
  or **ctp::view(** *contiguous range* **)** (implicit constructed)

Helper object which can be passed as an argument to **print/printf** to output a contiguous range.

.. code-block:: cpp

    int a[] = {1, 2, 3};
    ctp::print(ctp::view{a, 1}, ctp::view{a + 1, a + 3}, a);  // "[1] [2, 3] [1, 2, 3]\n"

* **ctp::formatter<** *Type* **>**

Specialize struct **ctp::formatter** for *Type*. Provide a function **constexpr auto format(** *Type* **);**
returning a tuple like object. The first element must be a format string followed by the arguments.

.. code-block:: cpp

    struct FooBar {
        int i;
    };

    template<>
    struct ctp::formatter<FooBar> {
        static constexpr auto format(const FooBar& obj) {
            return std::tuple{".i = {}", obj.i};
        }
    };

    constexpr auto test = ctp::print(FooBar{42});  // ".i = 42"

* **ctp::forward(** *value* **)** or **ctp::forward(** *function, arguments...* **)**

Helper to use **print/printf** in ``static_assert`` and template parameters. See `Known limitations`_.

compile-time-printer
++++++++++++++++++++

.. code-block::

    usage: compile-time-parser [optionals] [-- program args...]

    Compile-time printer - prints variables and types at compile time in C++.

    positional arguments:
      program               the program to compile the source (default: read from stdin)
      args                  the arguments for the command (default: [])

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      -r REMOVE, --remove REMOVE
                            removes matching regex from type info (default: [])
      -cr CAPTURE_REMOVE, --capture-remove CAPTURE_REMOVE
                            removes matching regex but keeps first capture-group from type info (default: [])
      --time-point          prints time point of each print statement (default: False)
      --no-color            disables colored error output stream (default: False)
      --hide-compiler-log   don't print unparsed compiler log (default: False)
      --dump-header-file    dumps the C++ header file to ctp/ctp.hpp (default: False)

Highlights
~~~~~~~~~~

* Use ``--time-point`` to get the time when the print statement has been reached. This can be used for benchmarking.

.. code-block::

    0:00:00.236446 - Function one evaluated.
    0:00:01.238051 - Function two evaluated.

* Use ``-r`` and ``-cr`` to remove unnecessary information from types:

.. code-block:: cpp

    namespace abc::def {
        template<typename T>
        struct holder {};
    }

    using H = abc::def::holder<int>;
    constexpr auto i = ctp::print(ctp::type<H>{});  // "abc::def::holder<int>"

Output with ``-r "abc::def::"``:

.. code-block::

    holder<int>

Output with ``-cr ".+<(.+)>"``:

.. code-block::

    int

How it works
------------

The implementation of **print/printf** does nothing more than forcing the compiler to generate warnings
depending on the passed arguments. The python tool parses the warnings and converts them back to the actually
C++ arguments and outputs them (standardized or formatted) to stdout or stderr.

So what does *-fpermissive* do and why do we use it?

    -fpermissive

    Downgrade some diagnostics about nonconformant code from errors to warnings. Thus, using -fpermissive will allow
    some nonconforming code to compile.

The nonconformant code we use in in the implementation is:

.. code-block:: cpp

    constexpr bool print(int i, int j) {
        int unused = i << j;
        return true;
    }

    constexpr auto test = print(10, 34);

``10 << 34`` will cause an integer overflow which is not allowed, especially in a constant expression.
GCC will output the following interesting diagnostic error:

    <source>:2:20: error: right operand of shift expression '(10 << 34)' is greater than or equal to the precision 32
    of the left operand [-fpermissive]

GCC evaluates the expression ``i << j`` and gives a detailed message about the value of ``i`` and ``j``.
Moreover, the error will recur, even for the same input. Let us all thank GCC for supporting old broken legacy code.
With *-fpermissive* this error becomes a warning and we can `continue compiling <https://gcc.godbolt.org/z/3G8h7M>`__.

So everything we like to print at compile-time and can be broken down to fundamental types, can be outputted.

Is it undefined behavior? Certainly. Will it format erase your hard drive? Probably not.

Use it only for development and not in production!

Known limitations
-----------------

Compiler
++++++++

Since GCC is the only compiler I am aware of with detailed diagnostic warnings to recur, this tool can only work with
GCC. `Prove me wrong. <https://github.com/Viatorus/compile-time-printer/issues/new>`__

Instantiation of static_assert or template parameter
++++++++++++++++++++++++++++++++++++++++++++++++++++

If a CTP statement is used while instantiate an expression triggered by a ``static_assert`` or a `template parameter`,
the compilation will fail without a meaningful error message:

.. code-block::

    <source>:55:19: error: non-constant condition for static assertion
        55 | static_assert(test());
           |               ~~~~^~

Because *-fpermissive* is a legacy option, it is not fully maintained anymore to work across all compile-time
instantiation.

One workaround is to forward the expression to a constexpr variable instantiation:

.. code-block:: cpp

    static_assert(ctp::forward<func()>);

Check out this `example <https://git.io/JLhaX>`__.

Caching
+++++++

The result of a constexpr functions could get cached. If this happens, a CTP statement will only be evaluated once.
Try to generate additional noise to prevent this. Especially if this happens in unevaluated context.
Add additional changing input to the function call as (template) parameter. Also, GCC >=10 added
``-fconstexpr-cache-depth=8``. Maybe a smaller value solves the issue.

Check out this `example <https://git.io/JLhVT>`__.

License
-------

`BSD-1 LICENSE <https://github.com/viatorus/compile-time-printer/blob/main/LICENSE.txt>`__
