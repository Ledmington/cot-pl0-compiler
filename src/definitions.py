from typing import Optional

from ir_node import IRNode
from symbol_table import standard_types


class Definition(IRNode):
    """Definitions base node"""

    def __init__(self, parent: Optional[IRNode] = None, symbol=None, body=None):
        super().__init__(parent, None, symbol, body)
        self.mapping = ["symbol"]


class FunctionDefinition(Definition):
    """Function Definition node"""

    def __init__(self, parent: Optional[IRNode] = None, symbol=None, body=None):
        super().__init__(parent, symbol, body)
        self.mapping = ["symbol", "body"]

    def get_global_symbols(self):
        return self.body.global_symtab.exclude(
            [standard_types["function"], standard_types["label"]]
        )

    def to_string(self, indent: str, indent_level: int) -> str:
        s = ""
        s += indent * indent_level + "FunctionDefinition {\n"
        indent_level += 1
        s += (
            indent * indent_level
            + "symbol: "
            + self.symbol.to_string(indent, indent_level + 1)
            + "\n"
        )
        s += (
            indent * indent_level
            + "body: "
            + self.body.to_string(indent, indent_level + 1)
            + "\n"
        )
        indent_level -= 1
        s += indent * indent_level + "}"
        return s
