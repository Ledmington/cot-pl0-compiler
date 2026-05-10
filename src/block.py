from typing import Callable, Optional

from definitions import Definition
from ir_node import IRNode
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
        self.defs.navigate(action, post)
        if post:
            action(self)

    def to_string(self, indent: str, indent_level: int) -> str:
        s = ""
        s += "Block {\n"
        indent_level += 1
        s += indent * indent_level + "definitions: {\n"
        for definition in self.defs:
            s += definition.to_string(indent, indent_level + 1) + "\n"
        s += indent * indent_level + "}\n"
        s += indent * indent_level + "body: {\n"
        for x in self.body:
            s += x.to_string(indent, indent_level + 1) + "\n"
        s += indent * indent_level + "}\n"
        indent_level -= 1
        s += indent * indent_level + "}"
        return s
