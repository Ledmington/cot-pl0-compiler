from lexer import Lexer, Token


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
        (Token.VAR, "var"),
        (Token.IDENT, "x"),
        (Token.COMMA, ","),
        (Token.IDENT, "squ"),
        (Token.SEMICOLON, ";"),
        (Token.PROCEDURE, "procedure"),
        (Token.IDENT, "square"),
        (Token.SEMICOLON, ";"),
        (Token.BEGIN, "begin"),
        (Token.IDENT, "squ"),
        (Token.BECOMES, ":="),
        (Token.IDENT, "x"),
        (Token.TIMES, "*"),
        (Token.IDENT, "x"),
        (Token.END, "end"),
        (Token.SEMICOLON, ";"),
        (Token.BEGIN, "begin"),
        (Token.IDENT, "x"),
        (Token.BECOMES, ":="),
        (Token.NUMBER, "1"),
        (Token.SEMICOLON, ";"),
        (Token.WHILE, "while"),
        (Token.IDENT, "x"),
        (Token.LEQ, "<="),
        (Token.NUMBER, "10"),
        (Token.DO, "do"),
        (Token.BEGIN, "begin"),
        (Token.CALL, "call"),
        (Token.IDENT, "square"),
        (Token.SEMICOLON, ";"),
        (Token.IDENT, "x"),
        (Token.BECOMES, ":="),
        (Token.IDENT, "x"),
        (Token.PLUS, "+"),
        (Token.NUMBER, "1"),
        (Token.SEMICOLON, ";"),
        (Token.PRINT, "!"),
        (Token.IDENT, "squ"),
        (Token.END, "end"),
        (Token.END, "end"),
        (Token.PERIOD, "."),
    ]
    assert expected == list(Lexer(input))
