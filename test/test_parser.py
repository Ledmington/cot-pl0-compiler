from statements import StatementList
from block import Block
from definitions import Definition
from symbol_table import Symbol, SymbolTable, Type, standard_types
from lexer import Lexer
from parser import parse_program


def test_parser():
    input = """VAR x, squ;
PROCEDURE square;
BEGIN
   squ := x * x
END;

BEGIN
   x := 1;
   WHILE x <= 10 DO
   BEGIN
      CALL square;
      x := x + 1 ;
            !squ
   END
END."""
    assert ... == parse_program(Lexer(input))


def test_parser2():
    input = """VAR x, y;."""
    assert Block(
        parent=None,
        gl_sym=None,
        lc_sym=None,
        defs=[
            Definition(symbol=Symbol("x", standard_types["int"])),
            Definition(symbol=Symbol("y", standard_types["int"])),
        ],
        body=StatementList(),
    ) == parse_program(Lexer(input))
