import logging
from typing import Optional

from block import Block
from constant import Constant
from debug_logger import debug_logger
from definitions import FunctionDefinition
from ir2 import (
    BinaryExpression,
    CallExpression,
    Expression,
    UnaryExpression,
)
from lexer import Lexer, Token
from statements import (
    AssignStatement,
    CallStatement,
    IfStatement,
    PrintStatement,
    Statement,
    StatementList,
    WhileStatement,
)
from symbol_table import Symbol, SymbolTable, standard_types
from variable import Variable

logger = logging.getLogger("parser")


sym = None  # current symbol
value = None  # current value
new_sym = None  # next symbol
new_value = None  # next value


def getsym(lexer: Lexer) -> int:
    """Update sym"""
    global new_sym
    global new_value
    global sym
    global value
    try:
        sym = new_sym
        value = new_value
        new_sym, new_value = next(lexer)
    except StopIteration:
        return 2
    logger.debug("getsym: {} {}".format(new_sym, new_value))
    return 1


def error(msg: str) -> None:
    logger.error(msg + " {} {}".format(new_sym, new_value))


def accept(lexer: Lexer, t: Token) -> int:
    logger.debug("accepting {} == {}".format(t, new_sym))
    return getsym(lexer) if new_sym == t else 0


def expect(lexer: Lexer, t: Token) -> int:
    logger.debug("expecting {}".format(t))
    if accept(lexer, t):
        return 1
    error("expect: unexpected symbol")
    return 0


@debug_logger
def factor(lexer: Lexer, symtab: SymbolTable):
    if accept(lexer, Token.IDENT):
        return Variable(var=symtab.find(value), symtab=symtab)
    if accept(lexer, Token.NUMBER):
        return Constant(value=value, symtab=symtab)
    elif accept(lexer, Token.LPAREN):
        expr = expression(lexer, symtab)
        expect(lexer, Token.RPAREN)
        return expr
    else:
        error("factor: syntax error")
        getsym(lexer)
        return None


@debug_logger
def term(lexer: Lexer, symtab: SymbolTable):
    op = None
    expr = factor(lexer, symtab)
    while new_sym in [Token.TIMES, Token.SLASH]:
        getsym(lexer)
        op = sym
        expr2 = factor(lexer, symtab)
        expr = BinaryExpression(operator=op, op1=expr, op2=expr2, symtab=symtab)
    return expr


@debug_logger
def expression(lexer: Lexer, symtab: SymbolTable) -> Expression:
    op = None
    if new_sym in [Token.PLUS, Token.MINUS]:
        getsym(lexer)
        op = sym
    expr = term(lexer, symtab)
    if op:
        expr = UnaryExpression(operand=expr, symtab=symtab)
    while new_sym in [Token.PLUS, Token.MINUS]:
        getsym(lexer)
        op = sym
        expr2 = term(lexer, symtab)
        expr = BinaryExpression(operator=op, op1=expr, op2=expr2, symtab=symtab)
    return expr


@debug_logger
def condition(lexer: Lexer, symtab: SymbolTable):
    if accept(lexer, Token.ODD):
        return UnaryExpression(operand=expression(lexer, symtab), symtab=symtab)
    else:
        expr = expression(lexer, symtab)
        if new_sym in ["eql", "neq", "lss", "leq", "gtr", "geq"]:
            getsym(lexer)
            logger.debug("condition operator {} {}".format(sym, new_sym))
            op = sym
            expr2 = expression(lexer, symtab)
            return BinaryExpression(
                operator=op, op1=expr, op2=expr2, symtab=symtab
            )
        else:
            error("condition: invalid operator")
            getsym(lexer)
            return None


@debug_logger
def statement(lexer: Lexer, symtab: SymbolTable) -> Optional[Statement]:
    if accept(lexer, Token.IDENT):
        target = symtab.find(value)
        expect(lexer, Token.BECOMES)
        expr = expression(lexer, symtab)
        return AssignStatement(target=target, expr=expr, symtab=symtab)
    elif accept(lexer, Token.CALL):
        expect(lexer, Token.IDENT)
        return CallStatement(
            call_expr=CallExpression(
                function=symtab.find(value), symtab=symtab
            ),
            symtab=symtab,
        )
    elif accept(lexer, Token.BEGIN):
        statement_list = StatementList(symtab=symtab)
        statement_list.append(statement(lexer, symtab))
        while accept(lexer, Token.SEMICOLON) == 0:
            statement_list.append(statement(symtab))
        expect(lexer, Token.END)
        statement_list.print_content()
        return statement_list
    elif accept(lexer, Token.IF):
        cond = condition(lexer, symtab)
        expect(lexer, Token.THEN)
        then = statement(lexer, symtab)
        return IfStatement(cond=cond, thenpart=then, symtab=symtab)
    elif accept(lexer, Token.WHILE):
        cond = condition(lexer, symtab)
        expect(lexer, Token.DO)
        body = statement(lexer, symtab)
        return WhileStatement(cond=cond, body=body, symtab=symtab)
    elif accept(lexer, Token.PRINT):
        expect(lexer, Token.IDENT)
        return PrintStatement(symbol=symtab.find(value), symtab=symtab)

    return None


@debug_logger
def block(lexer: Lexer, symtab: SymbolTable) -> Block:
    local_vars = SymbolTable()
    defs = []
    if accept(lexer, Token.CONST):
        expect(lexer, Token.IDENT)
        name = value
        expect(lexer, Token.EQL)
        expect(lexer, Token.NUMBER)
        local_vars.append(Symbol(name, standard_types["int"]))  # , value)
        while accept(lexer, Token.COMMA):
            expect(lexer, Token.IDENT)
            name = value
            expect(lexer, Token.EQL)
            expect(lexer, Token.NUMBER)
            local_vars.append(Symbol(name, standard_types["int"]))  # , value)
        expect(lexer, Token.SEMICOLON)
    if accept(lexer, Token.VAR):
        expect(lexer, Token.IDENT)
        local_vars.append(Symbol(value, standard_types["int"]))
        while accept(lexer, Token.COMMA):
            expect(lexer, Token.IDENT)
            local_vars.append(Symbol(value, standard_types["int"]))
        expect(lexer, Token.SEMICOLON)
    while accept(lexer, Token.PROCEDURE):
        expect(lexer, Token.IDENT)
        fname = value
        expect(lexer, Token.SEMICOLON)
        local_vars.append(Symbol(fname, standard_types["function"]))
        fbody = block(lexer, local_vars)
        expect(lexer, Token.SEMICOLON)
        defs.append(
            FunctionDefinition(symbol=local_vars.find(fname), body=fbody)
        )
    the_block = Block(gl_sym=symtab, lc_sym=local_vars, defs=defs, body=None)
    stat = statement(lexer, local_vars)
    the_block.body = stat
    return the_block


@debug_logger
def parse_program(lexer: Lexer) -> Block:
    """Axiom"""
    global_symtab = SymbolTable()
    getsym(lexer)
    the_program = block(lexer, global_symtab)
    expect(lexer, Token.PERIOD)
    return the_program
