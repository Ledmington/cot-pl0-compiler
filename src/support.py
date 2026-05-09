import logging

__doc__ = """Support functions for visiting the AST
These functions expose high level interfaces (passes) for actions that can be applied to multiple IR nodes."""

from pathlib import Path
from typing import Any, Callable

from block import Block
from lexer import Lexer
from st import getRegister, standard_types
from statements import (
    AssignStatement,
    BranchStatement,
    EmptyStatement,
    IfStatement,
    Statement,
    StatementList,
    StoreStatement,
    UnaryStatement,
    WhileStatement,
)


def get_node_list(root: Block):
    """Get a list of all nodes in the AST"""

    def register_nodes(node_list):
        def r(node):
            if node not in node_list:
                node_list.append(node)

        return r

    node_list = []
    root.navigate(register_nodes(node_list))
    return node_list


def get_symbol_tables(root):
    """Get a list of all symtabs in the AST"""

    def register_nodes(node_list):
        """Gets an empty symtab list, returns a function that populates it"""

        def r(node):
            """Given a node, adds its symbol table to the list"""
            try:
                if node.symtab not in node_list:
                    node_list.append(node.symtab)
            except Exception:
                pass
            try:
                if node.lc_sym not in node_list:
                    node_list.append(node.symtab)
            except Exception:
                pass

        return r

    node_list = []
    root.navigate(register_nodes(node_list))
    return node_list


def lowering(node) -> None:
    """Lowering action for a node
    (all high level nodes can be lowered to lower-level representation"""
    try:
        logging.debug("Lowering {} {}".format(type(node), id(node)))
        check = lower(node)
        if not check:
            logging.debug("Failed!")
    except Exception as e:
        logging.debug("Cannot lower {} {}".format(type(node), e))


def lower(stmt: WhileStatement) -> bool:
    out_label = standard_types["label"]()
    back_label = standard_types["label"]()
    end = EmptyStatement()
    end.set_label(out_label)
    reg = getRegister()
    stmt.symtab.append(reg)
    branch_out = BranchStatement(
        stmt.parent,
        Lexer.negate_operator(stmt.cond.operator),
        reg,
        out_label,
        stmt.symtab,
    )
    branch_back = BranchStatement(
        stmt.parent, None, None, back_label, stmt.symtab
    )
    stmt.cond.set_label(back_label)
    logging.debug("{} attached to {}".format(stmt.cond.get_label(), stmt.cond))
    slist = StatementList(
        stmt.parent,
        children=[stmt.cond, branch_out, stmt.body, branch_back, end],
    )
    return stmt.parent.replace(stmt, slist)


def lower(stmt: AssignStatement) -> bool:
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


def flattening(node):
    """Flattening action for a node
    (only StatList nodes are actually flattened)"""
    try:
        check = node.flatten()
        logging.debug("Flattening {} {}".format(type(node), id(node)))
        if not check:
            logging.debug("Failed!")
    except Exception as e:
        logging.debug("{} {}".format(type(node), e))


def layout(node):
    """Flattening action for a node
    (only StatList nodes are actually flattened)"""
    try:
        check = node.dataLayout()
        logging.debug("Data Layout {} {}".format(type(node), id(node)))
        if not check:
            logging.debug("Failed!")
    except Exception as e:
        logging.debug("{} {}".format(type(node), e))


def codegeneration(node):
    """Code generation for a node
    Prevents errors from blocking execution as some nodes do not need to generate anything
    """
    logging.info("Generating code for {} {}".format(type(node), id(node)))
    try:
        print(node.get_label().codegen(), ":")
    except Exception:
        print("\t")
    try:
        check = node.codegen()
        if check is None:
            logging.debug("Failed!")
        print(check)
    except Exception as e:
        logging.debug("{} {}".format(type(node), e))


def dotty_wrapper(fout) -> Callable[..., str | Any]:
    """Main function for graphviz dot output generation"""

    def dotty_function(irnode):
        """A function to print out the dot output"""
        attrs = {
            "body",
            "cond",
            "thenpart",
            "elsepart",
            "call",
            "step",
            "expr",
            "target",
            "defs",
        } & set(dir(irnode))

        res = repr(id(irnode)) + " ["
        if isinstance(irnode, Statement):
            res += "shape=box,"
        res += 'label="' + repr(type(irnode)) + " " + repr(id(irnode))

        try:
            res += ": " + irnode.value
        except Exception:
            pass

        try:
            res += ": " + irnode.name
        except Exception:
            pass

        try:
            res += ": " + getattr(irnode, "symbol").name
        except Exception:
            pass

        res += '" ];\n'

        if "children" in dir(irnode) and irnode.children:
            for node in irnode.children:
                res += (
                    repr(id(irnode))
                    + " -> "
                    + repr(id(node))
                    + " [pos="
                    + repr(irnode.children.index(node))
                    + "];\n"
                )
                if isinstance(node, str):
                    res += repr(id(node)) + " [label=" + node + "];\n"

        for d in attrs:
            node = getattr(irnode, d)
            if d == "target":
                res += (
                    repr(id(irnode))
                    + " -> "
                    + repr(id(node.value))
                    + " [label="
                    + node.name
                    + "];\n"
                )
            else:
                res += repr(id(irnode)) + " -> " + repr(id(node)) + ";\n"
        fout.write(res)
        return res

    return dotty_function


def print_dotty(root: Block, filename: Path) -> None:
    """Print a graphviz dot representation to file"""
    with open(filename, "w") as fout:
        fout.write("digraph G {\n")
        node_list = get_node_list(root)
        dotty = dotty_wrapper(fout)
        for n in node_list:
            dotty(n)
        fout.write("}\n")
