from __future__ import annotations


class Printer(object):
    """Utility class to print indented strings"""

    _buffer: str  # keeps the string content being constructed
    _indent: str  # indentation string
    _indent_level: int  # how many times to repeat the indentation string
    _at_line_start: bool  # tells whether the printer is currently printing the start of a line

    def __init__(self, indent: str = "  ") -> None:
        self._buffer = ""
        self._indent = indent
        self._indent_level = 0
        self._at_line_start = True

    def __iadd__(self, msg: str) -> Printer:
        for i, c in enumerate(msg):
            # apply indentation only when starting a new line
            if self._at_line_start:
                self._buffer += self._indent * self._indent_level
                self._at_line_start = False

            self._buffer += c

            self._at_line_start = c == "\n"

        return self

    def indent(self, indent_delta: int) -> None:
        self._indent_level += indent_delta
        assert self._indent_level >= 0

    def __repr__(self) -> str:
        assert self._indent_level == 0
        assert not self._at_line_start
        return self._buffer
