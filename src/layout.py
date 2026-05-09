import logging

from block import Block
from symbol_table import standard_types

logger = logging.getLogger("data_layout")


def layout(node):
    """Flattening action for a node
    (only StatList nodes are actually flattened)"""
    try:
        check = node.dataLayout()
        logger.debug("Data Layout {} {}".format(type(node), id(node)))
        if not check:
            logger.debug("Failed!")
    except Exception as e:
        logger.debug("{} {}".format(type(node), e))


def dataLayout(blk: Block) -> bool:
    if not blk.parent:
        for s in blk.symtab:
            if not s.storage_class and s.stype not in [
                standard_types["label"],
                standard_types["function"],
            ]:
                # anything that has not a storage class and is not a label or a function, we place in the global namespace
                s.storage_class = "global"
    else:
        # auto layout
        off = 0
        for s in blk.symtab:
            if not s.storage_class and s.stype not in [
                standard_types["label"],
                standard_types["function"],
            ]:
                s.storage_class = "auto"
                off += s.stype.size / 8
                s.offset = off
        blk.symtab.size = off

    return True
