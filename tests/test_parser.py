import math
import subprocess
import sys
from itertools import zip_longest

import pytest
from compile_time_printer.ctp import CTP, TypePrettifier, CompilerStatement

cpp_file = """
{}
#include <ctp/ctp.hpp>

{}

constexpr auto test() {{
    {}
    ctp::{}({});
    return 0;
}}

static_assert(test());
"""


def std_20_support():
    command = ['g++', '-std=c++20', '-fsyntax-only', '-xc++', '-']
    prog = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    prog.stdin.write('int main() {}'.encode('utf8'))
    prog.stdin.close()
    return prog.wait() == 0


def compile_file(input_file, std):
    command = ['g++', '-Iinclude', '-std={}'.format(std), '-fpermissive', '-fsyntax-only', '-xc++', '-']
    prog = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    prog.stdin.write(input_file.encode('utf8'))
    prog.stdin.close()

    for line in prog.stderr:
        yield line.decode('utf8')
    prog.stderr.close()


def compile_print_call(args, format=False, func_scope='', global_scope='', pre_include='', std='c++17'):
    if format:
        call = 'printf'
    else:
        call = 'print'
    args = [str(x) for x in args]
    return compile_file(cpp_file.format(pre_include, global_scope, func_scope, call, ', '.join(args)), std=std)


def assert_printers(log, expected, prettifier=None):
    prettifier = TypePrettifier([], []) if prettifier is None else prettifier
    ctp = CTP(prettifier, False)
    ctp.parse_error_log(log)
    for a, b in zip_longest(ctp.printers, expected):
        if a == b:
            continue
        if isinstance(a, CompilerStatement):
            assert a.serialize() == (b, True)
        else:
            assert a._format_str == b[0]
            assert a._output_stream == b[1]
            assert len(a._args) == len(b[2])
            for arg1, arg2 in zip(a._args, b[2]):
                if isinstance(arg2, float):
                    if math.isnan(arg1) and math.isnan(arg2):
                        return True
                    assert arg1 == pytest.approx(arg2)
                else:
                    assert arg1 == arg2


def test_empty():
    log = compile_print_call([])
    assert_printers(log, [(False, sys.stdout, [])])

    log = compile_print_call(['false'], pre_include='#define CTP_QUIET')
    assert_printers(log, [None])

    log = compile_print_call(['false'], pre_include='#define CTP_DEAD_QUIET')
    assert_printers(log, ['No CTP output found.\n'])


def test_bool():
    log = compile_print_call(['false'])
    assert_printers(log, [(False, sys.stdout, [False])])

    log = compile_print_call(['true'])
    assert_printers(log, [(False, sys.stdout, [True])])


def test_char():
    log = compile_print_call(["'x'"])
    assert_printers(log, [(False, sys.stdout, ['x'])])

    log = compile_print_call(["'\\n'"])
    assert_printers(log, [(False, sys.stdout, ['\n'])])

    log = compile_print_call(['c'], func_scope='const char& c = 32;')
    assert_printers(log, [(False, sys.stdout, [' '])])


def test_unicode():
    if std_20_support():
        log = compile_print_call(['char8_t(94)'], std='c++20')
        assert_printers(log, [(False, sys.stdout, ['^'])])

    log = compile_print_call(['char16_t(9822)'])
    assert_printers(log, [(False, sys.stdout, ['♞'])])

    log = compile_print_call(['char32_t(9822)'])
    assert_printers(log, [(False, sys.stdout, ['♞'])])

    log = compile_print_call(['"♞"'])
    assert_printers(log, [(False, sys.stdout, ['♞'])])

    log = compile_print_call(['u"♞"'])
    assert_printers(log, [(False, sys.stdout, ['♞'])])

    log = compile_print_call(['u8"♞"'])
    assert_printers(log, [(False, sys.stdout, ['♞'])])

    log = compile_print_call(['U"♞"'])
    assert_printers(log, [(False, sys.stdout, ['♞'])])

    log = compile_print_call(['"┌{0:─^{2}}┐\\n│{1: ^{2}}│\\n└{0:─^{2}}┘\\n"', '""', '"Hello, world!"', 20], format=True)
    assert_printers(log, [(True, sys.stdout, ['┌{0:─^{2}}┐\n│{1: ^{2}}│\n└{0:─^{2}}┘\n', '', 'Hello, world!', 20])])


def test_integer():
    log = compile_print_call([1])
    assert_printers(log, [(False, sys.stdout, [1])])

    log = compile_print_call([-1])
    assert_printers(log, [(False, sys.stdout, [-1])])

    log = compile_print_call(['0xF'])
    assert_printers(log, [(False, sys.stdout, [15])])

    log = compile_print_call(['123ULL'])
    assert_printers(log, [(False, sys.stdout, [123])])


def test_floating_point():
    log = compile_print_call([1.1])
    assert_printers(log, [(False, sys.stdout, [1.1])])

    log = compile_print_call(['1.2F'])
    assert_printers(log, [(False, sys.stdout, [1.2])])

    log = compile_print_call([345.654])
    assert_printers(log, [(False, sys.stdout, [345.654])])

    log = compile_print_call([-987.654])
    assert_printers(log, [(False, sys.stdout, [-987.654])])

    log = compile_print_call(['float(INFINITY)'])
    assert_printers(log, [(False, sys.stdout, [math.inf])])

    log = compile_print_call(['-float(INFINITY)'])
    assert_printers(log, [(False, sys.stdout, [-math.inf])])

    log = compile_print_call(['float(NAN)'])
    assert_printers(log, [(False, sys.stdout, [math.nan])])


def test_type():
    log = compile_print_call(['ctp::type<int>{}'])
    assert_printers(log, [(False, sys.stdout, ['int'])])

    log = compile_print_call(["ctp::type{'c'}"])
    assert_printers(log, [(False, sys.stdout, ['char'])])

    log = compile_print_call(['ctp::type<std::tuple<char>>{}'])
    assert_printers(log, [(False, sys.stdout, ['std::tuple<char>'])])

    log = compile_print_call(['ctp::type<std::tuple<char>>{}'])
    assert_printers(log, [(False, sys.stdout, ['tuple<char>'])], TypePrettifier(['std::'], []))

    log = compile_print_call(['ctp::type<std::tuple<char>>{}'])
    assert_printers(log, [(False, sys.stdout, ['tuple'])], TypePrettifier(['std::', '<char>'], []))

    log = compile_print_call(['ctp::type<std::tuple<char>>{}'])
    assert_printers(log, [(False, sys.stdout, ['std::<char>'])], TypePrettifier([], ['tuple(<char>)']))

    log = compile_print_call(['ctp::type<std::tuple<char>>{}'])
    assert_printers(log, [(False, sys.stdout, ['char'])], TypePrettifier([], ['.+<(.+)>']))

    log = compile_print_call(['ctp::type<std::tuple<char>>{}'])
    assert_printers(log, [(False, sys.stdout, ['char'])], TypePrettifier([], ['tuple(<char>)', 'std::<(char)>']))

    log = compile_print_call(['ctp::type<std::tuple<char>>{}'])
    assert_printers(log, [(False, sys.stdout, ['char'])], TypePrettifier(['std::'], ['tuple<(char)>']))

    log = compile_print_call(['ctp::type<int, float>{}'])
    assert_printers(log, [(False, sys.stdout, ['in, floa'])], TypePrettifier(['t'], []))

    log = compile_print_call(["ctp::type{1.0f, 'c'}"])
    assert_printers(log, [(False, sys.stdout, ['float, char'])])


def test_string():
    log = compile_print_call(['"hello"'])
    assert_printers(log, [(False, sys.stdout, ['hello'])])

    log = compile_print_call(['"how"', '"how"', '"are"', '"are"', '"you?"', '"you?"'])
    assert_printers(log, [(False, sys.stdout, ['how', 'how', 'are', 'are', 'you?', 'you?'])])


def test_array():
    log = compile_print_call(['x'], func_scope='int x[] = {1, 2, 3};')
    assert_printers(log, [(False, sys.stdout, [[1, 2, 3]])])

    log = compile_print_call(['std::array<int, 3>{{1, 2, 3}}'])
    assert_printers(log, [(False, sys.stdout, [[1, 2, 3]])])

    log = compile_print_call(['x'], func_scope='std::array<int, 3> x{{1, 2, 3}};')
    assert_printers(log, [(False, sys.stdout, [[1, 2, 3]])])

    log = compile_print_call(['x'], func_scope='const std::array<int, 3> x{{1, 2, 3}};')
    assert_printers(log, [(False, sys.stdout, [[1, 2, 3]])])

    log = compile_print_call(['x'], func_scope='std::array<std::array<int, 1>, 3> x{{1, 2, 3}};')
    assert_printers(log, [(False, sys.stdout, [[[1], [2], [3]]])])

    log = compile_print_call(['x'], func_scope='std::array<std::array<std::array<int, 1>, 1>, 3> x{{1, 2, 3}};')
    assert_printers(log, [(False, sys.stdout, [[[[1]], [[2]], [[3]]]])])

    log = compile_print_call(['x'], func_scope='std::array<std::string_view, 3> x{{{"ccdd"}, {"cd"}, {"cd"}}};')
    assert_printers(log, [(False, sys.stdout, [['ccdd', 'cd', 'cd']])])


def test_view():
    log = compile_print_call(['ctp::view<int>()'])
    assert_printers(log, [(False, sys.stdout, [[]])])

    log = compile_print_call(['ctp::view(x)'], func_scope='int x[] = {1, 2, 3};')
    assert_printers(log, [(False, sys.stdout, [[1, 2, 3]])])

    log = compile_print_call(['ctp::view(x, 2)'], func_scope='int x[] = {1, 2, 3};')
    assert_printers(log, [(False, sys.stdout, [[1, 2]])])

    log = compile_print_call(['ctp::view(x, 0)'], func_scope='int x[] = {1, 2, 3};')
    assert_printers(log, [(False, sys.stdout, [[]])])

    log = compile_print_call(['ctp::view(x + 1, x + 2)'], func_scope='int x[] = {1, 2, 3};')
    assert_printers(log, [(False, sys.stdout, [[2]])])

    log = compile_print_call(['ctp::view(x, x)'], func_scope='int x[] = {1, 2, 3};')
    assert_printers(log, [(False, sys.stdout, [[]])])

    log = compile_print_call(['ctp::view(x + 1, x)'], func_scope='int x[] = {1, 2, 3};')
    with pytest.raises(Exception):
        assert_printers(log, [])

    user_defined_container = """
    struct A {
        constexpr int* data() const {
            return g;
        }
        constexpr size_t size() const {
            return 3;
        }
        int g[4] = {4, 5, 6, 7};
    };
    """
    log = compile_print_call(['a'], func_scope='A a{};', global_scope=user_defined_container)
    assert_printers(log, [(False, sys.stdout, [[4, 5, 6]])])


def test_tuple_like():
    log = compile_print_call(['std::tuple{1, 2.0, "hello"}'])
    assert_printers(log, [(False, sys.stdout, [(1, 2.0, 'hello')])])

    log = compile_print_call(['std::pair{"hello", -2.0}'])
    assert_printers(log, [(False, sys.stdout, [('hello', -2.0)])])

    log = compile_print_call(['x'], func_scope='std::tuple x{1, 2.0, "hello"};')
    assert_printers(log, [(False, sys.stdout, [(1, 2.0, 'hello')])])

    log = compile_print_call(['x'], func_scope='std::tuple x{"abc", std::tuple{2.0}, std::tuple{-5.123}};')
    assert_printers(log, [(False, sys.stdout, [('abc', (2.0,), (-5.123,))])])


def test_format():
    log = compile_print_call(['"{}"', 1], format=True)
    assert_printers(log, [(True, sys.stdout, ['{}', 1])])


def test_output_stream():
    log = compile_print_call([1])
    assert_printers(log, [(False, sys.stdout, [1])])

    log = compile_print_call(['ctp::stdout', 1])
    assert_printers(log, [(False, sys.stdout, [1])])

    log = compile_print_call(['ctp::stderr', 1])
    assert_printers(log, [(False, sys.stderr, [1])])

    log = compile_print_call(['ctp::stdout', '"{}"', 1], format=True)
    assert_printers(log, [(True, sys.stdout, ['{}', 1])])

    log = compile_print_call(['ctp::stderr', '"{}"', 1], format=True)
    assert_printers(log, [(True, sys.stderr, ['{}', 1])])


def test_user_defined_type():
    outer_scope = """
    struct A{{}};
    template<>
    struct ctp::formatter<A> {{
        static constexpr auto format(const A& a) {{
            return {};
        }}
    }};
    """
    log = compile_print_call(['1, A{}'], global_scope=outer_scope.format('std::tuple("{}", 1)'))
    assert_printers(log, [(False, sys.stdout, [1, '1'])])

    log = compile_print_call(['1, A{}, 2'], global_scope=outer_scope.format('std::tuple("{}", 1)'))
    assert_printers(log, [(False, sys.stdout, [1, '1', 2])])

    log = compile_print_call(['A{}'], global_scope=outer_scope.format('std::tuple("abc")'))
    assert_printers(log, [(False, sys.stdout, ['abc'])])

    log = compile_print_call(['A{}'], global_scope=outer_scope.format('std::tuple("{}, {}, {}", 1, 2, 3)'))
    assert_printers(log, [(False, sys.stdout, ['1, 2, 3'])])

    log = compile_print_call(['A{}'], global_scope=outer_scope.format('std::tuple(1)'))
    assert_printers(log, [(False, sys.stdout, [])])


if __name__ == '__main__':
    pass
