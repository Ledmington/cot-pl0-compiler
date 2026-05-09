from __future__ import annotations

import re
from enum import Enum
from typing import Iterator, Optional


class Token(Enum):
    LPAREN = ["("]
    RPAREN = [")"]
    TIMES = ["*"]
    SLASH = ["/"]
    PLUS = ["+"]
    MINUS = ["-"]
    EQL = ["="]
    NEQ = ["!="]
    LSS = ["<"]
    LEQ = ["<="]
    GTR = [">"]
    GEQ = [">="]
    CALL = ["call"]
    BEGIN = ["begin"]
    SEMICOLON = [";"]
    END = ["end"]
    IF = ["if"]
    WHILE = ["while"]
    BECOMES = [":="]
    THEN = ["then"]
    DO = ["do"]
    CONST = ["const"]
    COMMA = [","]
    VAR = ["var"]
    PROCEDURE = ["procedure"]
    PERIOD = ["."]
    ODD = ["odd"]
    PRINT = ["!", "print"]
    NUMBER = []
    IDENT = []

    @classmethod
    def from_word(cls, word: str) -> Token:
        for token in cls:
            if word in token.value:
                return token
        try:
            float(word)
            return cls.NUMBER
        except ValueError:
            return cls.IDENT


class Lexer(Iterator[tuple[Token, str]]):
    """Simple lazy lexer for PL/0"""

    def __init__(self, text: str) -> None:
        self.text = text
        self._iterator: Optional[Iterator[tuple[Token, str]]] = None

    def _generate(self) -> Iterator[tuple[Token, str]]:
        t = re.split(r"(\W+)", self.text)
        text = " ".join(t)
        words = (w.strip() for w in text.lower().split())

        for word in words:
            if word:
                yield Token.from_word(word), word

    def __iter__(self) -> Lexer:
        self._iterator = self._generate()
        return self

    def __next__(self) -> tuple[Token, str]:
        if self._iterator is None:
            self._iterator = self._generate()
        return next(self._iterator)
