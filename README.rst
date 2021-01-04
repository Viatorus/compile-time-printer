.. image:: https://raw.githubusercontent.com/Viatorus/compile-time-printer/develop/web/static/banner-web.svg
    :alt: compile-time printer

Compile-Time Printer
====================

**Compile-Time Printer** prints values and types at compile-time in C++.

Teaser
------

+-------------------------------------------------+-------------------------------------------------+
|                       test.cpp                  |             Output at compile-time.             |
+-------------------------------------------------+-------------------------------------------------+
| .. code-block:: cpp                             | .. code-block:: none                            |
|                                                 |                                                 |
|     #include <ctp/ctp.hpp>                      |     .                                           |
|                                                 |                                                 |
|     template<auto I>                            |                                                 |
|     constexpr auto test(int i) {                |                                                 |
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
|     constexpr auto t = test<22>(20);            |                                                 |
|                                               . |                                               . |
+-------------------------------------------------+-------------------------------------------------+

Try it out online: https://viatorus.github.io/compile-time-printer/

Install
-------

To get started, all you need is the `python tool <https://pypi.org/project/compile-time-printer>`_:

.. code-block:: bash

    pip install compile-time-printer

Afterwards, dump the CTP header file and include it in your project:

.. code-block:: bash

    compile-time-printer --dump-header-file

Alternative, you can install the header file via the `conan package <https://bintray.com/viatorus/compile-time-printer>`_.

Finally, run CTP with your build command.

*With make*

.. code-block:: bash

    compile-time-printer -- make test.cpp

*With g++ directly*

.. code-block:: bash

    compile-time-printer -- g++ -I. -fsyntax-only -std=c++17 -fpermissive test.cpp

CTP requires `-fpermissive <https://gcc.gnu.org/onlinedocs/gcc/C_002b_002b-Dialect-Options.html>`_ in order to work.

Requirements
------------

* Python >=3.6
* GCC >=7.4 and STD >=C++17, -fpermissive

How it works
------------



Limitations
-----------

Compiler
++++++++

Since GCC is the only compiler I am aware of with detailed diagnostic warnings to recur, this tool can only work with
GCC.

Instantiation of static_assert or template parameter
++++++++++++++++++++++++++++++++++++++++++++++++++++

If a CTP statement is used while instantiate an expression triggered by a ``static_assert`` or a `template parameter`,
the compilation will fail without a meaningful error message:

.. code-block:: none

    <source>:55:19: error: non-constant condition for static assertion
        55 | static_assert(test());
           |               ~~~~^~

Because *-fpermissive* is a legacy option, it is not fully maintained anymore to work across all compile-time
instantiation.

One workaround is to forward the expression to a constexpr variable instantiation:

.. code-block:: cpp

    static_assert(ctp::forward<test()>);

See URL for a complete example.

Caching
+++++++

The result of a constexpr functions could get cached. If this happens, a print statement will only evaluated once.
Try to generate additional noise to prevent this. Especially if this happens in unevaluated context.
Add additional changing input to the function call as (template) parameter. Also, GCC >=10 added
``-fconstexpr-cache-depth=8`` as default caching value. Maybe a smaller value solves the issue.

See fibonacci.
