from __future__ import annotations


class Printer(object):
    """Utility class to print indented strings"""

    _buffer: str
    _indent: str
    _indent_level: int

    def __init__(self, indent: str = "  "):
        self._buffer = ""
        self._indent = indent
        self._indent_level = 0

    def __iadd__(self, msg: str) -> Printer:
        for c in msg:
            if c == "\n":
                msg += self._indent * self._indent_level
            msg += c
        return self

    def indent(self, indent_delta: int):
        self._indent_level += indent_delta
        assert self._indent_level >= 0

    def __repr__(self) -> str:
        return self._buffer
