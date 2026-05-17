from typing import Optional

from ir_node import IRNode
from printer import Printer
from symbol_table import standard_types


class Definition(IRNode):
    """Definitions base node"""

    def __init__(self, parent: Optional[IRNode] = None, symbol=None, body=None):
        super().__init__(parent, None, symbol, body)
        self.mapping = ["symbol"]

    def to_string(self, printer: Printer = Printer()) -> str:
        printer += "Definition {\n"
        printer.indent(1)
        printer += "symbol: " + self.symbol.to_string()
        printer += "body: " + self.body.to_string()
        printer.indent(-1)
        printer += "}"
        return printer.__repr__()


class FunctionDefinition(Definition):
    """Function Definition node"""

    def __init__(self, parent: Optional[IRNode] = None, symbol=None, body=None):
        super().__init__(parent, symbol, body)
        self.mapping = ["symbol", "body"]

    def get_global_symbols(self):
        return self.body.global_symtab.exclude(
            [standard_types["function"], standard_types["label"]]
        )

    def to_string(self, printer: Printer = Printer()):
        printer += "FunctionDefinition {\n"
        printer.indent(1)
        printer += "symbol: " + str(self.symbol) + "\n"
        printer += "body: "
        self.body.to_string(printer)
        printer += "\n"
        printer.indent(-1)
        printer += "}"
