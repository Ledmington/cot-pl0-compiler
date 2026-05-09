from typing import Optional

from ir_node import IRNode
from symbol_table import SymbolTable


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
