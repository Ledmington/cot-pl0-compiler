import logging

from statements import StatementList

logger = logging.getLogger("flattening")


def flattening(node):
    """Flattening action for a node
    (only StatList nodes are actually flattened)"""
    try:
        check = flatten(node)
        logger.debug("Flattening {} {}".format(type(node), id(node)))
        if not check:
            logger.debug("Failed!")
    except Exception as e:
        logger.debug("{} {}".format(type(node), e))


def flatten(stmt_list: StatementList):
    """Remove nested StatLists"""
    if isinstance(stmt_list.parent, StatementList):
        logger.debug(
            "Flattening {} into {}".format(id(stmt_list), id(stmt_list.parent))
        )
        for c in stmt_list.children:
            c.parent = stmt_list.parent
        i = stmt_list.parent.children.index(stmt_list)
        stmt_list.parent.children = (
            stmt_list.parent.children[:i]
            + stmt_list.children
            + stmt_list.parent.children[i + 1 :]
        )
        return True
    else:
        logger.debug(
            "Not flattening {} into {} of type {}".format(
                id(stmt_list), id(stmt_list.parent), type(stmt_list.parent)
            )
        )
        return False
