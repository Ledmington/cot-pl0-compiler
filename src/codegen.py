import logging

from statements import Statement
from symbol_table import LabelSymbol, Symbol

logger = logging.getLogger("codegen")


def codeGeneration(node):
    """Code generation for a node
    Prevents errors from blocking execution as some nodes do not need to generate anything
    """
    logger.info("Generating code for {} {}".format(type(node), id(node)))
    try:
        print(node.get_label().codegen(), ":")
    except Exception:
        print("\t")
    try:
        check = node.codegen()
        if check is None:
            logger.debug("Failed!")
        print(check)
    except Exception as e:
        logger.debug("{} {}".format(type(node), e))


def codegen(stmt: Statement) -> str:
    """Fallback implementation for codegen"""
    return stmt.__repr__()


def codegen(sym: Symbol) -> str:
    if sym.storage_class == "const":
        return "#{}".format(sym.value)
    if sym.storage_class == "global":
        return sym.name
    if sym.storage_class == "register" and sym.register is not None:
        return "r{}".format(sym.register)
    if sym.storage_class == "auto":
        return "#{}".format(
            sym.offset - 4
        )  # bit of a hack (this 4 should be taken from a config file, but it's fine for this toy compiler)
    return sym.name


def codegen(lbl: LabelSymbol) -> str:
    return lbl.name
