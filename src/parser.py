import logging
from typing import Optional

from ast import ProgramNode
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
    AssignmentStatement,
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


class Parser(object):
    _current_token: Token
    _current_value: str
    _next_token: Token
    _next_value: str

    def __init__(self, lexer: Lexer):
        self._lexer = lexer

    def get_symbol(self) -> int:
        """Update sym"""
        try:
            self._current_token = self._next_token
            self._current_value = self._next_value
            self._next_token, self._next_value = next(self._lexer)
        except StopIteration:
            return 2
        logger.debug(
            "get_symbol: {} {}".format(self._next_token, self._next_value)
        )
        return 1

    def error(self, msg: str) -> None:
        logger.error(msg + " {} {}".format(self._next_token, self._next_value))
        raise Exception()

    def accept(self, t: Token) -> int:
        logger.debug("accepting {} == {}".format(t, self._next_token))
        return self.get_symbol() if self._next_token == t else 0

    def expect(self, t: Token) -> int:
        logger.debug("expecting {}".format(t))
        if self.accept(t):
            return 1
        self.error("expect: unexpected symbol")
        return 0

    @debug_logger
    def parse_factor(self, symtab: SymbolTable) -> ...:
        if self.accept(Token.IDENT):
            return Variable(var=symtab.find(self._current_value), symtab=symtab)
        if self.accept(Token.NUMBER):
            return Constant(value=self._current_value, symtab=symtab)
        elif self.accept(Token.LPAREN):
            expr = self.parse_expression(symtab)
            self.expect(Token.RPAREN)
            return expr

        self.error("factor: syntax error")
        self.get_symbol()

    @debug_logger
    def parse_term(self, symtab: SymbolTable):
        expr = self.parse_factor(symtab)
        while self._next_token in [Token.TIMES, Token.SLASH]:
            self.get_symbol()
            op = self._current_token
            expr2 = self.parse_factor(symtab)
            expr = BinaryExpression(
                operator=op, op1=expr, op2=expr2, symtab=symtab
            )
        return expr

    @debug_logger
    def parse_expression(self, symtab: SymbolTable) -> Expression:
        op = None
        if self._next_token in [Token.PLUS, Token.MINUS]:
            self.get_symbol()
            op = self._current_token
        expr = self.parse_term(symtab)
        if op:
            expr = UnaryExpression(operand=expr, symtab=symtab)
        while self._next_token in [Token.PLUS, Token.MINUS]:
            self.get_symbol()
            op = self._current_token
            expr2 = self.parse_term(symtab)
            expr = BinaryExpression(
                operator=op, op1=expr, op2=expr2, symtab=symtab
            )
        return expr

    @debug_logger
    def parse_condition(self, symtab: SymbolTable):
        if self.accept(Token.ODD):
            return UnaryExpression(
                operand=self.parse_expression(symtab), symtab=symtab
            )
        else:
            expr = self.parse_expression(symtab)
            if self._next_token in ["eql", "neq", "lss", "leq", "gtr", "geq"]:
                self.get_symbol()
                logger.debug(
                    "condition operator {} {}".format(
                        self._current_token, self._next_token
                    )
                )
                op = self._current_token
                expr2 = self.parse_expression(symtab)
                return BinaryExpression(
                    operator=op, op1=expr, op2=expr2, symtab=symtab
                )
            else:
                self.error("condition: invalid operator")
                self.get_symbol()
                return None

    @debug_logger
    def parse_statement(self, symtab: SymbolTable) -> Statement:
        if self.accept(Token.IDENT):
            target = symtab.find(self._current_value)
            self.expect(Token.BECOMES)
            expr = self.parse_expression(symtab)
            return AssignmentStatement(target=target, expr=expr, symtab=symtab)
        elif self.accept(Token.CALL):
            self.expect(Token.IDENT)
            return CallStatement(
                call_expr=CallExpression(
                    function=symtab.find(self._current_value), symtab=symtab
                ),
                symtab=symtab,
            )
        elif self.accept(Token.BEGIN):
            statement_list = StatementList(symtab=symtab)
            statement_list.append(self.parse_statement(symtab))
            while self.accept(Token.SEMICOLON) == 0:
                statement_list.append(self.parse_statement(symtab))
            self.expect(Token.END)
            logger.debug(statement_list)
            return statement_list
        elif self.accept(Token.IF):
            cond = self.parse_condition(symtab)
            self.expect(Token.THEN)
            then = self.parse_statement(symtab)
            return IfStatement(cond=cond, thenpart=then, symtab=symtab)
        elif self.accept(Token.WHILE):
            cond = self.parse_condition(symtab)
            self.expect(Token.DO)
            body = self.parse_statement(symtab)
            return WhileStatement(cond=cond, body=body, symtab=symtab)
        elif self.accept(Token.PRINT):
            self.expect(Token.IDENT)
            return PrintStatement(
                symbol=symtab.find(self._current_value), symtab=symtab
            )

        self.error("statement: syntax error")

    @debug_logger
    def parse_program(self, symtab: SymbolTable) -> ProgramNode:
        local_vars = SymbolTable()
        defs = []
        if self.accept(Token.CONST):
            self.expect(Token.IDENT)
            name = self._current_value
            self.expect(Token.EQL)
            self.expect(Token.NUMBER)
            local_vars.append(Symbol(name, standard_types["int"]))  # , value)
            while self.accept(Token.COMMA):
                self.expect(Token.IDENT)
                name = self._current_value
                self.expect(Token.EQL)
                self.expect(Token.NUMBER)
                local_vars.append(
                    Symbol(name, standard_types["int"])
                )  # , value)
            self.expect(Token.SEMICOLON)
        if self.accept(Token.VAR):
            self.expect(Token.IDENT)
            local_vars.append(
                Symbol(self._current_value, standard_types["int"])
            )
            while self.accept(Token.COMMA):
                self.expect(Token.IDENT)
                local_vars.append(
                    Symbol(self._current_value, standard_types["int"])
                )
            self.expect(Token.SEMICOLON)
        while self.accept(Token.PROCEDURE):
            self.expect(Token.IDENT)
            fname = self._current_value
            self.expect(Token.SEMICOLON)
            local_vars.append(Symbol(fname, standard_types["function"]))
            fbody = self.parse_program(local_vars)
            self.expect(Token.SEMICOLON)
            defs.append(
                FunctionDefinition(symbol=local_vars.find(fname), body=fbody)
            )
        the_block = Block(
            gl_sym=symtab, lc_sym=local_vars, defs=defs, body=StatementList()
        )
        stat = self.parse_statement(local_vars)
        the_block.body = stat
        return the_block

    @debug_logger
    def parse_program(self) -> ProgramNode:
        """Axiom"""
        global_symtab = SymbolTable()
        self.get_symbol()
        the_program = self.parse_program(global_symtab)
        self.expect(Token.PERIOD)
        return the_program
