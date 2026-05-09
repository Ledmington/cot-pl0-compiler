from __future__ import annotations

from typing import Optional

from ir_node import IRNode
from st import SymbolTable


class Expression(IRNode):
    """Expression base node, characterized by an operator field"""

    pass

    def get_operator(self):
        return self.operator


class BinaryExpression(Expression):
    """Binary Expression node, characterized by an operator field and two operands"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        operator=None,
        op1=None,
        op2=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(BinaryExpression, self).__init__(
            parent, symtab, operator, op1, op2
        )
        self.mapping = ["operator", "op1", "op2"]

    def get_operands(self):
        return self.children[1:]


class UnaryExpression(Expression):
    """Unary Expression node, characterized by an operator field and an operand"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        operand=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(UnaryExpression, self).__init__(parent, symtab, operand, operand)
        self.mapping = ["operator", "operand"]

    def get_operand(self):
        return self.operand


class CallExpression(Expression):
    """Call Expression node, characterized by a target function and a parameters list"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        function=None,
        parameters=None,
        symtab: Optional[SymbolTable] = None,
    ):
        children = [function]
        if parameters:
            children += parameters
        super(CallExpression, self).__init__(parent, symtab, *children)
        self.mapping = ["function"]

    def get_target_function(self):
        return self.children[0]

    def get_parameters(self):
        return self.children[1:]


def subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in subclasses(c)]
    )
