import argparse
import datetime
import math
import pkgutil
import re
import subprocess
import sys
from enum import IntEnum
from pathlib import Path

try:
    from compile_time_printer import __version__
except ImportError:
    __version__ = 'unknown'

__author__ = 'Toni Neubert'
__copyright__ = 'Copyright 2021 %s' % __author__
__license__ = 'BSL-1.0'

from typing import List, TextIO, Iterator

PROTOCOL_VERSION = 1
PROTOCOL_VERSION_INDICATOR_RE = re.compile(
    r'In instantiation of .constexpr auto ctp::detail::print_protocol_version\(\) \[with int Version = (\d+)]')
START_INDICATOR_RE = re.compile(r' in .?constexpr.? expansion of .ctp::detail::print_start_indicator<')
END_INDICATOR_RE = re.compile(r' in .?constexpr.? expansion of .ctp::detail::print_end_indicator<')
PRINT_INDICATOR_RE = re.compile(
    r'^.+in .?constexpr.? expansion of .ctp::detail::print_value<(.+?), const (ctp::detail::)?separator_t&.+$')
VALUE_INDICATOR_RE = re.compile(r'right operand of shift expression .\((.+?) << (.+?)\).')

# Matches for reducing warning outputs related to CTP.
IN_EXPANSION_OF_CTP_MACRO_RE = re.compile(r'.+note: in expansion of macro .CTP_INTERNAL_PRINT.')
IN_EXPANSION_OF_RE = re.compile(r'.+:\s+in.+expansion.+of.+')
IN_TEMPLATE_ARGUMENT_FOR_TYPE = re.compile(r'.+note:\s+in template argument for type.+')
IN_INSTANTIATION_OF_RE = re.compile(r'.+: In instantiation of.+:')
IN_FUNCTION_RE = re.compile(r'.+: In function.+:')
AT_GLOBAL_SCOPE_RE = re.compile(r'.+: At global scope:')
IN_FILE_INCLUDED_RE = re.compile(r'(?:In file included|\s{16}) from .+')


class Indicator(IntEnum):
    Version = 32
    StartOut = 33
    StartErr = 34
    StartOutFormat = 35
    StartErrFormat = 36
    End = 37
    NaNFloat = 128
    PositiveInfinityFloat = 129
    NegativeInfinityFloat = 130
    NegativeFloat = 131
    PositiveFloat = 132
    FractionFloat = 133
    PositiveInteger = 134
    NegativeInteger = 135
    Type = 136
    ArrayBegin = 138
    ArrayEnd = 139
    StringBegin = 140
    StringEnd = 141
    TupleBegin = 142
    TupleEnd = 143
    CustomFormatBegin = 144
    CustomFormatEnd = 145


class TypePrettifier:
    """
    Removes unwanted type information.
    """

    def __init__(self, removes: List[str], capture_removes: List[str]):
        """
        Constructor.
        :param removes: list of regex to remove from type information
        :param capture_removes: list of regex to remove from type information with one capture to keep
        """
        self.__removes_re = [re.compile(r) for r in removes]
        self.__capture_removes = [re.compile(r) for r in capture_removes]

    def prettify(self, line):
        for replace_re in self.__removes_re:
            line = replace_re.sub('', line)
        for capture_replace_re in self.__capture_removes:
            line = capture_replace_re.sub(r'\1', line)
        return line


class PrintStatement:
    def __init__(self, time_point: datetime.timedelta, format_str: bool, output_stream: TextIO, args: List):
        self._time_point = time_point
        self._format_str = format_str
        self._output_stream = output_stream
        self._args = args

        if self._format_str:
            # First argument is format string.
            self._message = self._args[0].format(*self._args[1:])
        else:
            self._message = ' '.join(str(x) for x in self._args) + '\n'

    def serialize(self):
        return self._message, self._output_stream == sys.stderr

    def print(self, time_point: bool, colored: bool):
        """
        Prints all parsed arguments.
        :param time_point: if add timepoint to output
        :param colored: if output should be colored
        """
        string = ''
        if time_point:
            string += '{} - '.format(self._time_point)
        string += self._message
        if colored and self._output_stream == sys.stderr:
            string = '\033[1;31m{}\033[0m'.format(string)

        # Print statement.
        print(string, end='', file=self._output_stream)


class CompilerStatement:
    def __init__(self, message: str):
        self._message = message

    def serialize(self):
        return self._message, True

    def print(self, _1, _2):
        print(self._message, end='', file=sys.stderr)


class CTP:
    def __init__(self, type_prettifier: TypePrettifier, print_compiler_log: bool):
        """
        :param print_compiler_log: flag to enable printing unparsed compiler log
        """
        self._type_prettifier = type_prettifier
        self._printers = []
        self._print_compiler_log = print_compiler_log
        self._compiler_log = []

    @property
    def printers(self):
        self._process_compiler_log()
        return self._printers

    def parse_error_log(self, compiler_log: Iterator[str]) -> Iterator[PrintStatement]:
        """
        Parses for print statements in the compiler log.
        :param compiler_log: the compiler_log
        :param type_prettifier: the type prettifier
        :return: the print statements
        """
        not_available = True
        start_time = datetime.datetime.now()

        # For debugging only:
        # def logger():
        #     while True:
        #         try:
        #             line = next(compiler_log)
        #             print(line)
        #             yield line
        #         except StopIteration:
        #             break
        # log = logger()
        log = compiler_log

        while True:
            try:
                line = next(log)
            except StopIteration:
                break

            # Find start indicator.
            if START_INDICATOR_RE.search(line):
                time_diff = datetime.datetime.now() - start_time

                line = next(log)
                if 'error:' in line:
                    raise Exception('Parsing not possible. Did you forget -fpermissive?')
                value_match = VALUE_INDICATOR_RE.search(line)
                if value_match:
                    start_indicator = Indicator(int(value_match[2]))
                else:
                    raise Exception('No valid start indicator: {}'.format(line))
                output_stream = sys.stdout if start_indicator in [Indicator.StartOut,
                                                                  Indicator.StartOutFormat] else sys.stderr
                format_str = start_indicator in [Indicator.StartOutFormat, Indicator.StartErrFormat]
                args = self._parse_print_log(log)

                self._clean_compiler_log_prefix()
                self._printers.append(PrintStatement(time_diff, format_str, output_stream, args))
            else:
                version_match = PROTOCOL_VERSION_INDICATOR_RE.search(line)
                if version_match:
                    cpp_protocol_version = int(version_match[1])
                    if cpp_protocol_version != PROTOCOL_VERSION:
                        raise Exception(
                            'Incompatible CTP versions: C++ v{} <-> Python v{}'.format(cpp_protocol_version,
                                                                                       PROTOCOL_VERSION))
                    not_available = False
                    next(log)  # required from here
                    next(log)  # warning: unused variable ...
                    next(log)  # line | int version = Version;
                    next(log)  # ...  |     ^~~~~~~
                else:
                    self._compiler_log.append(line)
        if not_available:
            self._printers.append(CompilerStatement('No CTP output found.\n'))

        self._clean_compiler_log_suffix()

    def _process_compiler_log(self):
        if self._print_compiler_log:
            for cl in self._compiler_log:
                self._printers.append(CompilerStatement(cl))
        self._compiler_log = []

    def _clean_compiler_log_prefix(self):
        # Remove all in expansion related warnings.
        while len(self._compiler_log) > 0 and IN_EXPANSION_OF_RE.match(self._compiler_log[-1]):
            self._compiler_log.pop()

        # Remove all in instantiation related warnings.
        if len(self._compiler_log) > 0 and (
                AT_GLOBAL_SCOPE_RE.match(
                    self._compiler_log[-1]) or IN_FUNCTION_RE.match(self._compiler_log[-1])):
            self._compiler_log.pop()
        elif len(self._compiler_log) > 1 and IN_INSTANTIATION_OF_RE.match(self._compiler_log[-2]):
            self._compiler_log.pop()
            self._compiler_log.pop()

        # Remove in file included from.
        while len(self._compiler_log) > 0 and IN_FILE_INCLUDED_RE.match(self._compiler_log[-1]):
            self._compiler_log.pop()

        # Remove all in template arguments for type warnings.
        while len(self._compiler_log) > 0 and IN_TEMPLATE_ARGUMENT_FOR_TYPE.match(self._compiler_log[0]):
            self._compiler_log.pop(0)
            self._compiler_log.pop(0)
            self._compiler_log.pop(0)

        self._process_compiler_log()

    def _clean_compiler_log_suffix(self):
        # Remove all in template arguments for type warnings.
        while len(self._compiler_log) > 0 and IN_TEMPLATE_ARGUMENT_FOR_TYPE.match(self._compiler_log[0]):
            self._compiler_log.pop(0)
            self._compiler_log.pop(0)
            self._compiler_log.pop(0)

        # Remove in file included from.
        while len(self._compiler_log) > 0 and IN_FILE_INCLUDED_RE.match(self._compiler_log[-1]):
            self._compiler_log.pop()

        self._process_compiler_log()

    def _parse_print_log(self, log: Iterator[str]):
        """
        Parses for the parameters in the print log.
        :param log: the print log
        :param type_prettifier: Prettifier for types
        """
        stack: List = [[]]

        def parse_value(type_of_value: str, number: int, indicator: Indicator):
            """
            Logic of a shift-reduce parser.
            :param type_of_value: the type of the value
            :param number: a representation of the value as number
            :param indicator: the indicator
            :return:
            """
            if indicator == Indicator.NaNFloat:
                stack[-1].append(math.nan)
            elif indicator == Indicator.PositiveInfinityFloat:
                stack[-1].append(math.inf)
            elif indicator == Indicator.NegativeInfinityFloat:
                stack[-1].append(-math.inf)
            elif indicator == Indicator.PositiveFloat:
                stack.append(number)
            elif indicator == Indicator.NegativeFloat:
                stack.append(-number)
            elif indicator == Indicator.FractionFloat:
                num = stack.pop()
                factor = 1 if num >= 0 else -1
                num += factor * float(number) / math.pow(10, 18)
                stack[-1].append(num)
            elif indicator == Indicator.PositiveInteger:
                if type_of_value == 'char':
                    stack[-1].append(chr(number))
                elif type_of_value == 'bool':
                    stack[-1].append(bool(number))
                else:
                    stack[-1].append(number)
            elif indicator == Indicator.NegativeInteger:
                stack[-1].append(-number)
            elif indicator == Indicator.Type:
                stack[-1].append(self._type_prettifier.prettify(type_of_value))
            elif indicator in [Indicator.ArrayBegin, Indicator.StringBegin, indicator.TupleBegin]:
                stack.append([])
            elif indicator == Indicator.ArrayEnd:
                array = stack.pop()
                stack[-1].append(array)
            elif indicator == Indicator.StringEnd:
                array = stack.pop()
                stack[-1].append(''.join(array))
            elif indicator == Indicator.TupleEnd:
                array = stack.pop()
                stack[-1].append(tuple(array))
            elif indicator == Indicator.CustomFormatBegin:
                pass
            elif indicator == Indicator.CustomFormatEnd:
                # Unpack tuple.
                array = [*stack[-1].pop()]
                # First element is format string.
                stack[-1].append(array[0].format(*array[1:]))
            else:
                raise Exception('Unexpected indicator: {}'.format(int(indicator)))

        type_to_print = None
        for line in log:
            # Find a print indicator followed by a value indicator.
            if type_to_print:
                value_match = VALUE_INDICATOR_RE.search(line)
                if value_match:
                    parse_value(type_to_print, int(value_match[1]), Indicator(int(value_match[2])))
                    type_to_print = None
                    continue
            print_value_match = PRINT_INDICATOR_RE.match(line)
            if print_value_match:
                type_to_print = print_value_match[1]
            elif type_to_print:
                # Neither value indicator nor print indicator after a print indicator is an error.
                raise Exception('No valid print statement: {}'.format(line))
            elif END_INDICATOR_RE.search(line):
                break
        self._read_until_end_of_ctp_output(log)

        if len(stack) != 1:
            raise Exception('Incomplete print statement')
        return stack.pop()

    @staticmethod
    def _read_until_end_of_ctp_output(log: Iterator[str]):
        """
        Reads until the end of a fpermissive warning.
        :param log: the print log
        """
        try:
            while True:
                line = next(log)
                if IN_EXPANSION_OF_CTP_MACRO_RE.match(line):
                    next(log)
                    next(log)
                    break
        except StopIteration:
            return


def run_command(command: List[str], print_stdout: bool, return_code: List[int]) -> Iterator[str]:
    """
    Runs the given command in a subprocess and returns the error log.
    :param command: the command to run
    :param print_stdout: flag to enable printing stdout
    :param return_code: return/status/exit code of the ran command
    :return: the error log
    """
    if command:
        prog = subprocess.Popen(command, stdout=None if print_stdout else subprocess.PIPE, stderr=subprocess.PIPE)

        for line in prog.stderr:
            yield line.decode('utf8')
        return_code[0] = prog.wait()
    else:
        for line in sys.stdin:
            yield line


def parse_args(args: List):
    """
    Parses the command line parameters.
    :param args: command line parameters
    :return: `argparse.Namespace`: command line parameters namespace
    """

    class DistinctType:
        """
        Class is used to check if an argument was defaulted or not to improve error handling.
        """

        def __init__(self, name):
            self.__name = name

        def __str__(self):
            return self.__name

    distinct_program = DistinctType('read from stdin')

    parser = argparse.ArgumentParser(
        prog='compile-time-parser',
        description='Compile-time printer - prints variables and types at compile time in C++.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage='%(prog)s [optionals] [-- program args...]')
    parser.add_argument('--version', action='version', version='compile-time-parser {ver}'.format(ver=__version__))
    parser.add_argument('-r', '--remove', action='append', type=str,
                        help='removes matching regex from type info', default=[])
    parser.add_argument('-cr', '--capture-remove', action='append', type=str,
                        help='removes matching regex but keeps first capture-group from type info', default=[])
    parser.add_argument('--time-point', action='store_true',
                        help='prints time point of each print statement')
    parser.add_argument('--no-color', action='store_true',
                        help='disables colored error output stream')
    parser.add_argument('--hide-compiler-log', action='store_true',
                        help="don't print unparsed compiler log")
    parser.add_argument('program', type=str, nargs='?',
                        help='the program to compile the source', default=distinct_program)
    parser.add_argument('args', type=str, nargs='*',
                        help='the arguments for the command', default=[])
    parser.add_argument('--dump-header-file', action='store_true',
                        help='dumps the C++ header file to ctp/ctp.hpp')

    # Arguments after '--' are the program and arguments called as subprocess.
    # They are not passed to the argument parser and therefore have to be separated.
    prog_and_args = None
    try:
        i = args.index('--')
        prog_and_args = args[i + 1:]
        args = args[:i]
    except ValueError:
        pass

    options = parser.parse_args(args)
    if options.program is not distinct_program:
        parser.error('program and args must be placed after --')

    options.prog_and_args = prog_and_args
    return options


def dump_header_file():
    p = Path('ctp')
    p.mkdir(exist_ok=True)
    data = pkgutil.get_data('compile_time_printer', 'include/ctp/ctp.hpp')
    (p / 'ctp.hpp').write_bytes(data)


def main(args: List[str]):
    """"
    Main entry point allowing external calls.
    :param args: command line parameter list
    :param print_fct: function to print
    """
    options = parse_args(args)

    if options.dump_header_file:
        dump_header_file()
        print('Header file has been placed under ctp/ctp.hpp.')
        return

    # Run command.
    return_code = [0]
    log = run_command(options.prog_and_args, not options.hide_compiler_log, return_code)

    # Parse output.
    type_prettifier = TypePrettifier(options.remove, options.capture_remove)
    ctp = CTP(type_prettifier, not options.hide_compiler_log)
    try:
        ctp.parse_error_log(log)
    except Exception as e:
        return_code[0] = e

    # Iterate over printers and print.
    for printer in ctp.printers:
        printer.print(options.time_point, not options.no_color)
    if return_code[0] != 0:
        sys.exit(return_code[0])


def run():
    """
    Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == '__main__':
    run()
