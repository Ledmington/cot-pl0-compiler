from typing import Callable, Optional

from ir_node import IRNode
from st import SymbolTable, standard_types
from statement import Statement
from statements import FunctionPrologueStatement, ReturnStatement, StatementList


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

    def lower(self) -> None:
        if not self.parent:  # Global Block
            new_pr = FunctionPrologueStatement()
            new_ep = ReturnStatement()
            stlist = StatementList(
                self,
                children=[new_pr, self.body, new_ep],
                symtab=self.body.symtab,
            )
            self.body = stlist
            self.body.setLabel(standard_types["label"]("main"))

    def dataLayout(self) -> bool:
        if not self.parent:
            for s in self.symtab:
                if not s.storage_class and s.stype not in [
                    standard_types["label"],
                    standard_types["function"],
                ]:
                    # anything that has not a storage class and is not a label or a function, we place in the global namespace
                    s.storage_class = "global"
        else:
            # auto layout
            off = 0
            for s in self.symtab:
                if not s.storage_class and s.stype not in [
                    standard_types["label"],
                    standard_types["function"],
                ]:
                    s.storage_class = "auto"
                    off += s.stype.size / 8
                    s.offset = off
            self.symtab.size = off

        return True

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
