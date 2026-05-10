from typing import Optional

from ir_node import IRNode
from symbol_table import standard_types


class Definition(IRNode):
    """Definitions base node"""

    def __init__(self, parent: Optional[IRNode] = None, symbol=None):
        super(Definition, self).__init__(parent, None, symbol)
        self.mapping = ["symbol"]


class FunctionDefinition(Definition):
    """Function Definition node"""

    def __init__(self, parent: Optional[IRNode] = None, symbol=None, body=None):
        super(Definition, self).__init__(parent, None, symbol, body)
        self.mapping = ["symbol", "body"]

    def get_global_symbols(self):
        return self.body.global_symtab.exclude(
            [standard_types["function"], standard_types["label"]]
        )
