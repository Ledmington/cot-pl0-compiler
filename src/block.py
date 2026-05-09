from typing import Callable, Optional

from ir_node import IRNode
from statements import Statement
from symbol_table import SymbolTable, standard_types


class Block(Statement):
    """Scope block node"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        gl_sym: Optional[SymbolTable] = None,
        lc_sym: Optional[SymbolTable] = None,
        defs=None,
        body=None,
    ):
        lc_sym.setParent(gl_sym)
        super(Block, self).__init__(parent, lc_sym, defs, body)
        self.mapping = ["defs", "body"]

    def navigate(
        self, action: Callable[[IRNode], None], post: bool = False
    ) -> None:
        """Redefine navigate to force main to be generated before other functions"""
        if not post:
            action(self)
        self.body.navigate(action, post)
        self.defs.navigate(action, post)
        if post:
            action(self)
