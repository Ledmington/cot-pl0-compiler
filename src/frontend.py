#!/usr/bin/python

__doc__ = """PL/0 recursive descent parser adapted from Wikipedia"""

import argparse
import os
import logging
from pathlib import Path

import ir2

# ir2.setup("arm_ir")  # configurable target
from ir2 import (
    BinaryExpression,
    UnaryExpression,
    WhileStatement,
    AssignStatement,
    IfStatement,
    Variable,
    Constant,
    CallExpression,
)
from ir2 import (
    FunctionDefinition,
    DefinitionList,
    Block,
    CallStatement,
    StatementList,
    PrintStatement,
)
from logger import logger
import lexer

from st import standard_types, Symbol, SymbolTable

logging.basicConfig(filename="error.log", level=logging.DEBUG)

symbols = lexer.symbols.keys()


sym = None  # current symbol
value = None  # current value
new_sym = None  # next symbol
new_value = None  # next value


def getsym(lexer) -> int:
    """Update sym"""
    global new_sym
    global new_value
    global sym
    global value
    try:
        sym = new_sym
        value = new_value
        new_sym, new_value = lexer.__next__()
    except StopIteration:
        return 2
    logging.debug("getsym: {} {}".format(new_sym, new_value))
    return 1


def error(msg):
    logging.error(msg + " {} {}".format(new_sym, new_value))


def accept(lexer, s: str) -> int:
    logging.debug("accepting {} == {}".format(s, new_sym))
    return getsym(lexer) if new_sym == s else 0


def expect(lexer, s) -> int:
    logging.debug("expecting {}".format(s))
    if accept(lexer, s):
        return 1
    error("expect: unexpected symbol")
    return 0


@logger
def factor(symtab):
    if accept(lexer, "ident"):
        return Variable(var=symtab.find(value), symtab=symtab)
    if accept(lexer, "number"):
        return Constant(value=value, symtab=symtab)
    elif accept(lexer, "lparen"):
        expr = expression()
        expect(lexer, "rparen")
        return expr
    else:
        error("factor: syntax error")
        getsym(lexer)
        return None


@logger
def term(symtab):
    op = None
    expr = factor(symtab)
    while new_sym in ["times", "slash"]:
        getsym(lexer)
        op = sym
        expr2 = factor(symtab)
        expr = BinaryExpression(operator=op, op1=expr, op2=expr2, symtab=symtab)
    return expr


@logger
def expression(symtab):
    op = None
    if new_sym in ["plus", "minus"]:
        getsym(lexer)
        op = sym
    expr = term(symtab)
    if op:
        expr = UnaryExpression(operand=expr, symtab=symtab)
    while new_sym in ["plus", "minus"]:
        getsym(lexer)
        op = sym
        expr2 = term(symtab)
        expr = BinaryExpression(operator=op, op1=expr, op2=expr2, symtab=symtab)
    return expr


@logger
def condition(symtab):
    if accept(lexer, "oddsym"):
        return UnaryExpression(operand=expression(symtab), symtab=symtab)
    else:
        expr = expression(symtab)
        if new_sym in ["eql", "neq", "lss", "leq", "gtr", "geq"]:
            getsym(lexer)
            logging.debug("condition operator {} {}".format(sym, new_sym))
            op = sym
            expr2 = expression(symtab)
            return BinaryExpression(
                operator=op, op1=expr, op2=expr2, symtab=symtab
            )
        else:
            error("condition: invalid operator")
            getsym(lexer)
            return None


@logger
def statement(symtab):
    if accept(lexer, "ident"):
        target = symtab.find(value)
        expect(lexer, "becomes")
        expr = expression(symtab)
        return AssignStatement(target=target, expr=expr, symtab=symtab)
    elif accept(lexer, "callsym"):
        expect(lexer, "ident")
        return CallStatement(
            call_expr=CallExpression(
                function=symtab.find(value), symtab=symtab
            ),
            symtab=symtab,
        )
    elif accept(lexer, "beginsym"):
        statement_list = StatementList(symtab=symtab)
        statement_list.append(statement(symtab))
        while accept(lexer, "semicolon") == 0:
            statement_list.append(statement(symtab))
        expect(lexer, "endsym")
        statement_list.print_content()
        return statement_list
    elif accept(lexer, "ifsym"):
        cond = condition(symtab)
        expect(lexer, "thensym")
        then = statement(symtab)
        return IfStatement(cond=cond, thenpart=then, symtab=symtab)
    elif accept(lexer, "whilesym"):
        cond = condition(symtab)
        expect(lexer, "dosym")
        body = statement(symtab)
        return WhileStatement(cond=cond, body=body, symtab=symtab)
    elif accept(lexer, "print"):
        expect(lexer, "ident")
        return PrintStatement(symbol=symtab.find(value), symtab=symtab)

    return None


@logger
def block(symtab):
    local_vars = SymbolTable()
    defs = DefinitionList()
    if accept(lexer, "constsym"):
        expect(lexer, "ident")
        name = value
        expect(lexer, "eql")
        expect(lexer, "number")
        local_vars.append(Symbol(name, standard_types["int"]))  # , value)
        while accept(lexer, "comma"):
            expect(lexer, "ident")
            name = value
            expect(lexer, "eql")
            expect(lexer, "number")
            local_vars.append(Symbol(name, standard_types["int"]))  # , value)
        expect(lexer, "semicolon")
    if accept(lexer, "varsym"):
        expect(lexer, "ident")
        local_vars.append(Symbol(value, standard_types["int"]))
        while accept(lexer, "comma"):
            expect(lexer, "ident")
            local_vars.append(Symbol(value, standard_types["int"]))
        expect(lexer, "semicolon")
    while accept(lexer, "procsym"):
        expect(lexer, "ident")
        fname = value
        expect(lexer, "semicolon")
        local_vars.append(Symbol(fname, standard_types["function"]))
        fbody = block(local_vars)
        expect(lexer, "semicolon")
        defs.append(
            FunctionDefinition(symbol=local_vars.find(fname), body=fbody)
        )
    the_block = Block(gl_sym=symtab, lc_sym=local_vars, defs=defs, body=None)
    stat = statement(local_vars)
    the_block.body = stat
    return the_block  # Block(gl_sym=symtab, lc_sym=local_vars, defs=defs, body=stat)


@logger
def program(lexer):
    """Axiom"""
    global_symtab = SymbolTable()
    getsym(lexer)
    the_program = block(global_symtab)
    expect(lexer, "period")
    return the_program


def run(source, target="arm", root_dir: Path = Path(os.getcwd())):
    """Run the compiler pipeline."""
    target_info = ir2.setup(target + "_ir")  # configurable target
    the_lexer = lexer.lexer(source)
    res = program(the_lexer)
    from support import (
        lowering,
        flattening,
        codegeneration,
        print_dotty,
        layout,
    )

    res.navigate(lowering, post=True)
    res.navigate(flattening, post=True)
    logging.debug("\n {} \n".format(res))

    res.navigate(layout, post=True)

    print_dotty(res, root_dir / "log.dot")

    from cfg import CFG

    cfg = CFG(res)
    cfg.liveness()
    cfg.print_cfg_to_dot(root_dir / "cfg.dot")
    cfg.reg_alloc(n=target_info["available_registers"])

    res.navigate(codegeneration)


def main():
    parser = argparse.ArgumentParser(
        description="PL/0 recursive descent parser"
    )
    parser.add_argument("filename", help="Input source file")
    args = parser.parse_args()

    filename = args.filename
    logging.debug("Reading input source from {}".format(filename))
    source = open(filename, "r").read()

    logging.debug(
        """
*********************************************
    Starting debug with program '{}'
*********************************************
    """.format(filename)
    )

    logging.debug(
        """
***** Program '{}' source *****
{}
***** Program '{}' source *****
""".format(filename, source, filename)
    )

    root_dir = os.getcwd()

    run(source, root_dir=Path(root_dir))


if __name__ == "__main__":
    main()
