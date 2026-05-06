__doc__ = """Simple lexer for PL/0 using generators"""

from typing import Any, Generator

# Tokens can have multiple definitions if needed
symbols = {
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


def negate_operator(op: str) -> str | None:
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


def token(word: str) -> str:
    """Return corresponding token for a given word"""
    for s in symbols:
        if word in symbols[s]:
            return s
    try:  # If a terminal is not one of the standard tokens but can be converted to float, then it is a number, otherwise, an identifier
        float(word)
        return "number"
    except ValueError:
        return "ident"


def lexer(text: str) -> Generator[tuple[str, str], Any, None]:
    """Generator implementation of a lexer"""
    import re

    t = re.split("(\\W+)", text)  # Split at non-alphanumeric sequences
    text = " ".join(t)  # Join alphanumeric and non-alphanumeric, with spaces
    words = [w.strip() for w in text.lower().split()]  # Split tokens
    for word in words:
        yield token(word), word
