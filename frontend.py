#!/usr/bin/python

__doc__ = """PL/0 recursive descent parser adapted from Wikipedia"""

import logging
import ir2

ir2.setup("arm_ir")  # configurable target
from ir2 import BinExpr, UnExpr, WhileStat, AssignStat, IfStat, Var, Const, CallExpr
from ir2 import FunctionDef, DefinitionList, Block, CallStat, StatList, PrintStat
from logger import logger
import lexer

logging.basicConfig(filename="error.log", level=logging.DEBUG)
from st import standard_types, Symbol, SymbolTable

symbols = lexer.symbols.keys()


sym = None  # current symbol
value = None  # current value
new_sym = None  # next symbol
new_value = None  # next value

the_lexer = None


def getsym() -> int:
    """Update sym"""
    global new_sym
    global new_value
    global sym
    global value
    try:
        sym = new_sym
        value = new_value
        new_sym, new_value = the_lexer.__next__()
    except StopIteration:
        return 2
    logging.debug("getsym: {} {}".format(new_sym, new_value))
    return 1


def error(msg):
    logging.error(msg + " {} {}".format(new_sym, new_value))


def accept(s:str) -> int:
    logging.debug("accepting {} == {}".format(s, new_sym))
    return getsym() if new_sym == s else 0


def expect(s) -> int:
    logging.debug("expecting {}".format(s))
    if accept(s):
        return 1
    error("expect: unexpected symbol")
    return 0


@logger
def factor(symtab):
    if accept("ident"):
        return Var(var=symtab.find(value), symtab=symtab)
    if accept("number"):
        return Const(value=value, symtab=symtab)
    elif accept("lparen"):
        expr = expression()
        expect("rparen")
        return expr
    else:
        error("factor: syntax error")
        getsym()
        return None


@logger
def term(symtab):
    op = None
    expr = factor(symtab)
    while new_sym in ["times", "slash"]:
        getsym()
        op = sym
        expr2 = factor(symtab)
        expr = BinExpr(operator=op, op1=expr, op2=expr2, symtab=symtab)
    return expr


@logger
def expression(symtab):
    op = None
    if new_sym in ["plus", "minus"]:
        getsym()
        op = sym
    expr = term(symtab)
    if op:
        expr = UnExpr(operator=initial_op, operand=expr, symtab=symtab)
    while new_sym in ["plus", "minus"]:
        getsym()
        op = sym
        expr2 = term(symtab)
        expr = BinExpr(operator=op, op1=expr, op2=expr2, symtab=symtab)
    return expr


@logger
def condition(symtab):
    if accept("oddsym"):
        return UnExpr(operator="odd", operand=expression(symtab), symtab=symtab)
    else:
        expr = expression(symtab)
        if new_sym in ["eql", "neq", "lss", "leq", "gtr", "geq"]:
            getsym()
            logging.debug("condition operator {} {}".format(sym, new_sym))
            op = sym
            expr2 = expression(symtab)
            return BinExpr(operator=op, op1=expr, op2=expr2, symtab=symtab)
        else:
            error("condition: invalid operator")
            getsym()
            return None


@logger
def statement(symtab):
    if accept("ident"):
        target = symtab.find(value)
        expect("becomes")
        expr = expression(symtab)
        return AssignStat(target=target, expr=expr, symtab=symtab)
    elif accept("callsym"):
        expect("ident")
        return CallStat(
            call_expr=CallExpr(function=symtab.find(value), symtab=symtab),
            symtab=symtab,
        )
    elif accept("beginsym"):
        statement_list = StatList(symtab=symtab)
        statement_list.append(statement(symtab))
        while accept("semicolon") == 0:
            statement_list.append(statement(symtab))
        expect("endsym")
        statement_list.print_content()
        return statement_list
    elif accept("ifsym"):
        cond = condition(symtab)
        expect("thensym")
        then = statement(symtab)
        return IfStat(cond=cond, thenpart=then, symtab=symtab)
    elif accept("whilesym"):
        cond = condition(symtab)
        expect("dosym")
        body = statement(symtab)
        return WhileStat(cond=cond, body=body, symtab=symtab)
    elif accept("print"):
        expect("ident")
        return PrintStat(symbol=symtab.find(value), symtab=symtab)

    return None


@logger
def block(symtab):
    local_vars = SymbolTable()
    defs = DefinitionList()
    if accept("constsym"):
        expect("ident")
        name = value
        expect("eql")
        expect("number")
        local_vars.append(Symbol(name, standard_types["int"]))  # , value)
        while accept("comma"):
            expect("ident")
            name = value
            expect("eql")
            expect("number")
            local_vars.append(Symbol(name, standard_types["int"]))  # , value)
        expect("semicolon")
    if accept("varsym"):
        expect("ident")
        local_vars.append(Symbol(value, standard_types["int"]))
        while accept("comma"):
            expect("ident")
            local_vars.append(Symbol(value, standard_types["int"]))
        expect("semicolon")
    while accept("procsym"):
        expect("ident")
        fname = value
        expect("semicolon")
        local_vars.append(Symbol(fname, standard_types["function"]))
        fbody = block(local_vars)
        expect("semicolon")
        defs.append(FunctionDef(symbol=local_vars.find(fname), body=fbody))
    the_block = Block(gl_sym=symtab, lc_sym=local_vars, defs=defs, body=None)
    stat = statement(local_vars)
    the_block.body = stat
    return the_block  # Block(gl_sym=symtab, lc_sym=local_vars, defs=defs, body=stat)


@logger
def program():
    """Axiom"""
    global_symtab = SymbolTable()
    getsym()
    the_program = block(global_symtab)
    expect("period")
    return the_program


def run(source, target="arm"):
    """Run the compiler pipeline."""
    target_info = ir2.setup(target + "_ir")  # configurable target
    global the_lexer
    the_lexer = lexer.lexer(source)
    res = program()
    from support import lowering, flattening, codegeneration, print_dotty, layout

    res.navigate(lowering, post=True)
    res.navigate(flattening, post=True)
    logging.debug("\n {} \n".format(res))

    res.navigate(layout, post=True)

    print_dotty(res, "log.dot")

    from cfg import CFG

    cfg = CFG(res)
    cfg.liveness()
    cfg.print_cfg_to_dot("cfg.dot")
    cfg.reg_alloc(n=target_info["available_registers"])

    res.navigate(codegeneration)


if __name__ == "__main__":
    logging.debug("""
*********************************************
	Starting debug with standard test program
*********************************************
""")

    source = open("input.txt").read()

    run(source)
