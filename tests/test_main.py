import io
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager, redirect_stdout, redirect_stderr

import pytest

from compile_time_printer.ctp import main


def test_get_compiler_version(capsys):
    with capsys.disabled():
        subprocess.run(['g++', '--version'], check=True)


def test_version():
    with pytest.raises(SystemExit):
        main(['--version'])


def test_help():
    with pytest.raises(SystemExit):
        main(['--help'])


def test_program_and_args_wrong_passed():
    with pytest.raises(SystemExit):
        main(['make'])


@contextmanager
def cwd(path):
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)


def test_dump_files():
    try:
        os.symlink('../../include', 'src/compile_time_printer/include')
        with tempfile.TemporaryDirectory() as folder:
            with cwd(folder):
                assert not os.path.exists('ctp/ctp.hpp')
                main(['--dump-header-file'])
                assert os.path.exists('ctp/ctp.hpp')
    finally:
        os.unlink('src/compile_time_printer/include')


def test_no_args():
    p = subprocess.Popen(['python', 'src/compile_time_printer/ctp.py'], stderr=subprocess.PIPE)
    assert p.stderr.read().decode('utf8') == 'No CTP output found.\n'

    err = io.StringIO()
    with redirect_stderr(err):
        main(['--', 'cat', '/dev/null'])
    assert err.getvalue() == 'No CTP output found.\n'


def run_main(file, params=None, other=None, capture=True):
    if params is None:
        params = []
    if other is None:
        other = []
    command = ['--', 'g++', '-Iinclude', '-fsyntax-only', '-std=c++17', '-fpermissive', 'tests/data/' + file]
    if capture:
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            main(params + command + other)
        return out.getvalue(), err.getvalue()
    else:
        main(params + command + other)


def test_example_fibonacci():
    out, err = run_main('fibonacci.cpp')
    assert re.match(r'1 \+.* 0 = 8\n', out)
    assert not err


def test_example_fibonacci_with_noise():
    out, err = run_main('fibonacci_with_noise.cpp')
    assert out == '1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 0 = 8\n'
    assert not err


def test_example_user_defined_type():
    out, err = run_main('user_defined_type.cpp')
    assert out == 'Print type FooBar&. .i = 1, .i = 2.\n'
    assert not err


def test_example_user_defined_type_with_time_point():
    out, err = run_main('user_defined_type.cpp', ['--time-point'])
    assert re.match(r'\d:\d{2}:\d{2}.\d+ - Print type FooBar&. .i = 1, .i = 2.\n', out)
    assert not err


def test_example_user_defined_type_with_type_prettifier():
    out, err = run_main('user_defined_type.cpp', ['-r', '&'])
    assert out == 'Print type FooBar. .i = 1, .i = 2.\n'
    assert not err

    out, err = run_main('user_defined_type.cpp', ['-cr', '(.+Ba)r&'])
    assert out == 'Print type FooBa. .i = 1, .i = 2.\n'
    assert not err


def test_example_output_stream():
    out, err = run_main('output_stream.cpp')
    assert out == '1\n1\nLog 1\n'
    assert err == '\033[1;31m1\n\033[0m\033[1;31mLog 1\n\033[0m'

    out, err = run_main('output_stream.cpp', ['--no-color'])
    assert out == '1\n1\nLog 1\n'
    assert err == '1\nLog 1\n'


def test_example_type_stack():
    out, err = run_main('type_stack.cpp')
    assert out == 'stack<>\npush int\npush double\npush char\nstack<char, double, int>\n'
    assert not err


def test_example_value_stack():
    out, err = run_main('value_stack.cpp', ['--no-color'])
    assert out == '[0, 0, 0]\npush 2\npush 5\npush 7\n[2, 5, 7]\n'
    assert err == 'Stack overflow!\n'


def test_workarounds():
    out, err = run_main('workarounds.cpp')
    assert out == '1\n2\n3\n4\n1\n2\n3\n4\n'
    # TODO: assert err == ""


def test_missing_permissive():
    with pytest.raises(SystemExit, match='Parsing not possible. Did you forget -fpermissive?'):
        run_main('value_stack.cpp', other=['-fno-permissive'])


def test_hide_compiler_log():
    # With compiler log.
    out = io.StringIO()
    err = io.StringIO()
    with pytest.raises(SystemExit), redirect_stdout(out), redirect_stderr(err):
        run_main('user_defined_type.cpp', other=['-fno-syntax-only'], capture=False)
    assert 'undefined reference to `main' in err.getvalue()
    assert out.getvalue() == 'Print type FooBar&. .i = 1, .i = 2.\n'

    # Without compiler log.
    out = io.StringIO()
    err = io.StringIO()
    with pytest.raises(SystemExit), redirect_stdout(out), redirect_stderr(err):
        run_main('user_defined_type.cpp', ['--hide-compiler-log'], other=['-fno-syntax-only'], capture=False)
    assert not err.getvalue()
    assert out.getvalue() == 'Print type FooBar&. .i = 1, .i = 2.\n'


if __name__ == '__main__':
    pass
