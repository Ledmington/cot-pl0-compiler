import logging

__doc__ = """Support functions for visiting the AST
These functions expose high level interfaces (passes) for actions that can be applied to multiple IR nodes."""

from pathlib import Path

from typing import Any, Callable

from ir2 import Statement, Block


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


def lowering(node):
    """Lowering action for a node
    (all high level nodes can be lowered to lower-level representation"""
    try:
        check = node.lower()
        logging.debug("Lowering {} {}".format(type(node), id(node)))
        if not check:
            logging.debug("Failed!")
    except Exception as e:
        logging.debug("Cannot lower {} {}".format(type(node), e))


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
        print(node.getLabel().codegen(), ":")
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
