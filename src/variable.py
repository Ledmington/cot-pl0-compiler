from typing import Optional

from ir2 import LoadStatement
from ir_node import IRNode
from st import SymbolTable, getRegister


class Variable(IRNode):
    """Class representing read access to both local and global variables"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        var=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(Variable, self).__init__(parent, symtab, var)
        self.mapping = ["symbol"]

    def lower(self) -> bool:
        reg = getRegister()
        self.symtab.append(reg)
        node = LoadStatement(self.parent, self.symbol, reg, self.symtab)
        return self.parent.replace(self, node)
