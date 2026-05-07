from typing import Optional

from ir2 import LoadStatement
from ir_node import IRNode
from st import SymbolTable, getRegister, standard_types


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

    def lower(self) -> bool:
        reg = getRegister()
        self.symtab.append(reg)
        node = LoadStatement(self.parent, self.value, reg, self.symtab)
        return self.parent.replace(self, node)
