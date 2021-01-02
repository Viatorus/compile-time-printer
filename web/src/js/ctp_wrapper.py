import re

COMPILER_ERROR_WARNING_MESSAGE = re.compile(r'(<source>:)(\d+)')
COMPILER_ERROR_WARNING_MESSAGE_DETAIL = re.compile(r'^([ ]+)(\d+)([ ]+\|[ ]+)')


class CTPHelper:
    def __init__(self, include_offset):
        self._include_offset = include_offset

    def parse(self, log):
        error = None
        ctp = CTP(TypePrettifier([], []), True)  # noqa
        try:
            ctp.parse_error_log(iter(log))  # noqa
        except Exception as e:
            error = {'message': str(e), 'error_output': True, 'compiler_output': True}

        result = []
        for printer in ctp.printers:
            result.append(self._prepare(printer))

        if error:
            result.append(error)
        return result

    def _prepare(self, printer):
        message, error_output = printer.serialize()
        if isinstance(printer, PrintStatement):  # noqa
            return {'message': message, 'error_output': error_output, 'compiler_output': False}

        # Fix line number for compiler messages.
        [include_line_offset, include_line_nbr] = self._include_offset

        def fix_line_number(match):
            line_nbr = int(match[2])
            # Logs before include.
            if line_nbr <= include_line_nbr:
                return match[1] + match[2]
            # Logs in include.
            if (line_nbr - include_line_offset) <= 0:
                return match[1] + str(include_line_nbr)
            # Logs after include.
            return match[1] + str(line_nbr - include_line_offset)

        def fix_line_number_detail(match):
            line_nbr = int(match[2])
            # Logs before include.
            if line_nbr <= include_line_nbr:
                return match[1] + match[2] + match[3]
            # Logs in include.
            new_line_nbr = line_nbr - include_line_offset
            if new_line_nbr <= 0:
                new_line_nbr = include_line_nbr
            # Keep correct spacing.
            new_line_nbr = str(new_line_nbr)
            padding = len(match[1]) + len(match[2]) - len(new_line_nbr)
            return ' ' * padding + new_line_nbr + match[3]

        message, matched = COMPILER_ERROR_WARNING_MESSAGE.subn(fix_line_number, message)
        if not matched:
            message = COMPILER_ERROR_WARNING_MESSAGE_DETAIL.sub(fix_line_number_detail, message)
        return {'message': message + '\n', 'error_output': error_output, 'compiler_output': True}


def parse(include_offset, log):
    return CTPHelper(include_offset).parse(log)
