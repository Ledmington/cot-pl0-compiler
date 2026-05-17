from __future__ import annotations


class Printer(object):
    """Utility class to print indented strings"""

    _buffer: str  # keeps the string content being constructed
    _indent: str  # indentation string
    _indent_level: int  # how many times to repeat the indentation string
    _pending_newline: bool  # tells if the last character was a newline

    def __init__(self, indent: str = "  ") -> None:
        self._buffer = ""
        self._indent = indent
        self._indent_level = 0
        self._pending_newline = False

    def __iadd__(self, msg: str) -> Printer:
        if self._pending_newline:
            self._buffer += self._indent * self._indent_level
        self._pending_newline = msg[-1] == "\n"
        for i, c in enumerate(msg):
            self._buffer += c
            # adding indentation for every newline except the last one
            if c == "\n" and i != len(msg) - 1:
                self._buffer += self._indent * self._indent_level
        return self

    def indent(self, indent_delta: int) -> None:
        self._indent_level += indent_delta
        assert self._indent_level >= 0

    def __repr__(self) -> str:
        assert self._indent_level == 0
        assert not self._pending_newline
        return self._buffer
