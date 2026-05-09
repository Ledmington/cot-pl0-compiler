from typing import Optional

from ir_node import IRNode
from symbol_table import SymbolTable, standard_types


class Constant(IRNode):
    """Constant objects from the source code"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        value=0,
        symb=None,
        symtab: Optional[SymbolTable] = None,
    ):
        if not symb:
            try:
                symb = standard_types["int"](value=int(value))
            except Exception:
                symb = standard_types["float"](value=float(value))
        super(Constant, self).__init__(parent, symtab, symb)
        self.mapping = ["value"]
