from statements import StatementList
from block import Block
from definitions import Definition
from symbol_table import Symbol, SymbolTable, Type, standard_types
from lexer import Lexer
from parser import parse_program


def test_variable_declaration():
    input = """VAR x;."""
    expected = Program()
    actual = parse_program(Lexer(input))
    assert expected == actual


def test_example():
    # Taken from https://en.wikipedia.org/wiki/PL/0
    input = """var i, s;
begin
  i := 0; s := 0;
  while i < 5 do
  begin
    i := i + 1;
    s := s + i * i
  end
end."""
    expected = ...
    actual = parse_program(Lexer(input))
    assert expected == actual


def test_function_declaration():
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
    expected = ...
    actual = parse_program(Lexer(input))
    assert expected == actual


def test_function_call():
    # Taken from https://en.wikipedia.org/wiki/PL/0
    input = """const max = 100;
var arg, ret;

procedure isprime;
var i;
begin
	ret := 1;
	i := 2;
	while i < arg do
	begin
		if arg / i * i = arg then
		begin
			ret := 0;
			i := arg
		end;
		i := i + 1
	end
end;

procedure primes;
begin
	arg := 2;
	while arg < max do
	begin
		call isprime;
		if ret = 1 then write arg;
		arg := arg + 1
	end
end;

call primes
."""
    expected = ...
    actual = parse_program(Lexer(input))
    assert expected == actual


def test_complex():
    # Taken from https://en.wikipedia.org/wiki/PL/0
    input = """VAR x, y, z, q, r, n, f;

PROCEDURE multiply;
VAR a, b;
BEGIN
  a := x;
  b := y;
  z := 0;
  WHILE b > 0 DO
  BEGIN
    IF ODD b THEN z := z + a;
    a := 2 * a;
    b := b / 2
  END
END;

PROCEDURE divide;
VAR w;
BEGIN
  r := x;
  q := 0;
  w := y;
  WHILE w <= r DO w := 2 * w;
  WHILE w > y DO
  BEGIN
    q := 2 * q;
    w := w / 2;
    IF w <= r THEN
    BEGIN
      r := r - w;
      q := q + 1
    END
  END
END;

PROCEDURE gcd;
VAR f, g;
BEGIN
  f := x;
  g := y;
  WHILE f # g DO
  BEGIN
    IF f < g THEN g := g - f;
    IF g < f THEN f := f - g
  END;
  z := f
END;

PROCEDURE fact;
BEGIN
  IF n > 1 THEN
  BEGIN
    f := n * f;
    n := n - 1;
    CALL fact
  END
END;;
  ?x; ?y; CALL multiply; !z;
  ?x; ?y; CALL divide; !q; !r;
  ?x; ?y; CALL gcd; !z;
  ?n; f := 1; CALL fact; !f
END."""
    expected = ...
    actual = parse_program(Lexer(input))
    assert expected == actual
