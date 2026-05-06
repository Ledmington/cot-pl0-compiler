from __future__ import annotations

import re
from typing import Iterator, Optional


class Lexer(Iterator[tuple[str, str]]):
    """Simple lazy lexer for PL/0"""

    symbols: dict[str, list[str]] = {
        "lparen": ["("],
        "rparen": [")"],
        "times": ["*"],
        "slash": ["/"],
        "plus": ["+"],
        "minus": ["-"],
        "eql": ["="],
        "neq": ["!="],
        "lss": ["<"],
        "leq": ["<="],
        "gtr": [">"],
        "geq": [">="],
        "callsym": ["call"],
        "beginsym": ["begin"],
        "semicolon": [";"],
        "endsym": ["end"],
        "ifsym": ["if"],
        "whilesym": ["while"],
        "becomes": [":="],
        "thensym": ["then"],
        "dosym": ["do"],
        "constsym": ["const"],
        "comma": [","],
        "varsym": ["var"],
        "procsym": ["procedure"],
        "period": ["."],
        "oddsym": ["odd"],
        "print": ["!", "print"],
    }

    def __init__(self, text: str) -> None:
        self.text = text
        self._iterator: Optional[Iterator[tuple[str, str]]] = None

    def _generate(self) -> Iterator[tuple[str, str]]:
        t = re.split(r"(\W+)", self.text)
        text = " ".join(t)
        words = (w.strip() for w in text.lower().split())

        for word in words:
            if word:  # skip empty strings defensively
                yield self.token(word), word

    @staticmethod
    def negate_operator(op: str) -> Optional[str]:
        match op:
            case "eql":
                return "neq"
            case "neq":
                return "eql"
            case "lss":
                return "geq"
            case "leq":
                return "gtr"
            case "gtr":
                return "leq"
            case "geq":
                return "lss"
            case _:
                return None

    @classmethod
    def token(cls, word: str) -> str:
        for s, values in cls.symbols.items():
            if word in values:
                return s
        try:
            float(word)
            return "number"
        except ValueError:
            return "ident"

    def __iter__(self) -> Lexer:
        # create a fresh generator each time iteration starts
        self._iterator = self._generate()
        return self

    def __next__(self) -> tuple[str, str]:
        if self._iterator is None:
            self._iterator = self._generate()
        return next(self._iterator)
