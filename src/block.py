from typing import Callable, Optional

from definitions import Definition
from ir_node import IRNode
from printer import Printer
from statements import Statement, StatementList
from symbol_table import SymbolTable


class Block(Statement):
    """Scope block node"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        gl_sym: Optional[SymbolTable] = None,
        lc_sym: Optional[SymbolTable] = None,
        defs: list[Definition] = None,
        body: StatementList = None,
    ):
        if lc_sym:
            lc_sym.set_parent(gl_sym)
        super().__init__(parent, lc_sym, defs, body)
        self.mapping = ["defs", "body"]

    def navigate(
        self, action: Callable[[IRNode], None], post: bool = False
    ) -> None:
        """Redefine navigate to force main to be generated before other functions"""
        if not post:
            action(self)

        self.body.navigate(action, post)

        for definition in self.defs:
            definition.navigate(action, post)
        # self.defs.navigate(action, post)

        if post:
            action(self)

    def to_string(self, printer: Printer = Printer()) -> str:
        printer += "Block {\n"
        printer.indent(1)
        printer += "definitions: {\n"
        printer.indent(1)
        for definition in self.defs:
            printer += definition.to_string() + "\n"
        printer.indent(-1)
        printer += "}\n"
        printer += "body: {\n"
        printer.indent(1)
        for x in self.body:
            printer += x.to_string() + "\n"
        printer.indent(-1)
        printer += "}\n"
        printer.indent(-1)
        printer += "}"
        return printer.__repr__()
