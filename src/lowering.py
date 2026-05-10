import logging
from typing import Optional

from block import Block
from constant import Constant
from definitions import FunctionDefinition
from ir2 import BinaryExpression, CallExpression, UnaryExpression
from statements import (
    AssignmentStatement,
    BinaryStatement,
    BranchLinkStatement,
    BranchStatement,
    EmptyStatement,
    FunctionPrologueStatement,
    IfStatement,
    LoadStatement,
    ReturnStatement,
    StatementList,
    StoreStatement,
    UnaryStatement,
    WhileStatement,
)
from symbol_table import getRegister, standard_types
from variable import Variable

logger = logging.getLogger("lowering")


def lowering(node) -> None:
    """Lowering action for a node
    (all high level nodes can be lowered to lower-level representation"""
    try:
        logger.debug("Lowering {} {}".format(type(node), id(node)))
        check = lower(node)
        if not check:
            logger.debug("Failed!")
    except Exception as e:
        logger.debug("Cannot lower {} {}".format(type(node), e))


def lower(stmt: Block) -> None:
    if not stmt.parent:  # Global Block
        new_pr = FunctionPrologueStatement()
        new_ep = ReturnStatement()
        stlist = StatementList(
            stmt,
            children=[new_pr, stmt.body, new_ep],
            symtab=stmt.body.symtab,
        )
        stmt.body = stlist
        stmt.body.set_label(standard_types["label"]("main"))


def lower(func_def: FunctionDefinition):
    new_pr = FunctionPrologueStatement()
    new_ep = ReturnStatement()
    slist = StatementList(func_def, children=[new_pr, func_def.body, new_ep])
    func_def.body = slist


def lower(stmt: WhileStatement) -> bool:
    out_label = standard_types["label"]()
    back_label = standard_types["label"]()
    end = EmptyStatement()
    end.set_label(out_label)
    reg = getRegister()
    stmt.symtab.append(reg)
    branch_out = BranchStatement(
        stmt.parent,
        negate_operator(stmt.cond.operator),
        reg,
        out_label,
        stmt.symtab,
    )
    branch_back = BranchStatement(
        stmt.parent, None, None, back_label, stmt.symtab
    )
    stmt.cond.set_label(back_label)
    logger.debug("{} attached to {}".format(stmt.cond.get_label(), stmt.cond))
    slist = StatementList(
        stmt.parent,
        children=[stmt.cond, branch_out, stmt.body, branch_back, end],
    )
    return stmt.parent.replace(stmt, slist)


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


def lower(stmt: AssignmentStatement) -> bool:
    node = StoreStatement(stmt.parent, stmt.target, stmt.expr.dest, stmt.symtab)
    slist = StatementList(stmt.parent, children=[stmt.expr, node])
    return stmt.parent.replace(stmt, slist)


def lower(stmt: IfStatement) -> bool:
    if stmt.elsepart:
        raise Exception("Lowering of if-else not implemented yet!")
    out_label = standard_types["label"]()
    end = EmptyStatement()
    end.set_label(out_label)
    reg = getRegister()
    stmt.symtab.append(reg)
    ncond = UnaryStatement(stmt.parent, "-", reg, stmt.cond.dest, stmt.symtab)
    branch = BranchStatement(
        stmt.parent, stmt.cond.operator, ncond.dest, out_label, stmt.symtab
    )
    slist = StatementList(
        stmt.parent,
        children=[
            stmt.cond,
            ncond,
            branch,
            # thenpart,
            end,
        ],
    )
    return stmt.parent.replace(stmt, slist)


def lower(expr: UnaryExpression) -> bool:
    reg = getRegister()
    expr.symtab.append(reg)
    node = BinaryStatement(
        expr, expr.operator, reg, expr.operand.dest, expr.symtab
    )
    slist = StatementList(expr.parent, children=[expr.operand, node])
    return expr.parent.replace(expr, slist)


def lower(expr: BinaryExpression) -> bool:
    reg = getRegister()
    expr.symtab.append(reg)
    node = BinaryStatement(
        expr, expr.operator, reg, expr.op1.dest, expr.op2.dest, expr.symtab
    )
    slist = StatementList(expr.parent, children=[expr.op1, expr.op2, node])
    return expr.parent.replace(expr, slist)


def lower(expr: CallExpression) -> bool:
    node = BranchLinkStatement(
        expr.parent, None, None, expr.function, expr.symtab
    )
    return expr.parent.replace(expr, node)


def lower(const: Constant) -> bool:
    reg = getRegister()
    const.symtab.append(reg)
    node = LoadStatement(const.parent, const.value, reg, const.symtab)
    return const.parent.replace(const, node)


def lower(var: Variable) -> bool:
    reg = getRegister()
    var.symtab.append(reg)
    node = LoadStatement(var.parent, var.symbol, reg, var.symtab)
    return var.parent.replace(var, node)
