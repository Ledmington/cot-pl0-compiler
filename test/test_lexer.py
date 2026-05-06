from lexer import lexer


def test_lexer():
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
    expected = [
        ("varsym", "var"),
        ("ident", "x"),
        ("comma", ","),
        ("ident", "squ"),
        ("semicolon", ";"),
        ("procsym", "procedure"),
        ("ident", "square"),
        ("semicolon", ";"),
        ("beginsym", "begin"),
        ("ident", "squ"),
        ("becomes", ":="),
        ("ident", "x"),
        ("times", "*"),
        ("ident", "x"),
        ("endsym", "end"),
        ("semicolon", ";"),
        ("beginsym", "begin"),
        ("ident", "x"),
        ("becomes", ":="),
        ("number", "1"),
        ("semicolon", ";"),
        ("whilesym", "while"),
        ("ident", "x"),
        ("leq", "<="),
        ("number", "10"),
        ("dosym", "do"),
        ("beginsym", "begin"),
        ("callsym", "call"),
        ("ident", "square"),
        ("semicolon", ";"),
        ("ident", "x"),
        ("becomes", ":="),
        ("ident", "x"),
        ("plus", "+"),
        ("number", "1"),
        ("semicolon", ";"),
        ("print", "!"),
        ("ident", "squ"),
        ("endsym", "end"),
        ("endsym", "end"),
        ("period", "."),
    ]
    assert expected == list(lexer(input))
