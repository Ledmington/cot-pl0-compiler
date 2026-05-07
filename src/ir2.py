from __future__ import annotations

from typing import Optional

from ir_node import IRNode
from st import SymbolTable, getRegister, standard_types
from statements import (
    BinaryStatement,
    BranchLinkStat,
    FunctionPrologueStatement,
    ReturnStatement,
    StatementList,
)

# EXPRESSION


class Expression(IRNode):
    """Expression base node, characterized by an operator field"""

    pass

    def getOperator(self):
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

    def getOperands(self):
        return self.children[1:]

    def lower(self) -> bool:
        reg = getRegister()
        self.symtab.append(reg)
        node = BinaryStatement(
            self, self.operator, reg, self.op1.dest, self.op2.dest, self.symtab
        )
        slist = StatementList(self.parent, children=[self.op1, self.op2, node])
        return self.parent.replace(self, slist)


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

    def getOperand(self):
        return self.operand

    def lower(self) -> bool:
        reg = getRegister()
        self.symtab.append(reg)
        node = BinaryStatement(
            self, self.operator, reg, self.operand.dest, self.symtab
        )
        slist = StatementList(self.parent, children=[self.operand, node])
        return self.parent.replace(self, slist)


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

    def getTargetFunction(self):
        return self.children[0]

    def getParameters(self):
        return self.children[1:]

    def lower(self) -> bool:
        node = BranchLinkStat(
            self.parent, None, None, self.function, self.symtab
        )
        return self.parent.replace(self, node)


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

    def getGlobalSymbols(self):
        return self.body.global_symtab.exclude(
            [standard_types["function"], standard_types["label"]]
        )

    def lower(self):
        new_pr = FunctionPrologueStatement()
        new_ep = ReturnStatement()
        slist = StatementList(self, children=[new_pr, self.body, new_ep])
        self.body = slist


class DefinitionList(IRNode):
    """List of definitions"""

    def __init__(self, parent: Optional[IRNode] = None, children=[]):
        super(DefinitionList, self).__init__(parent, None, *children)

    def append(self, elem: IRNode):
        elem.parent = self
        self.children.append(elem)


def subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in subclasses(c)]
    )


if __name__ == "__main__":
    TEST = CallExpression(function="pippo", parameters=["pluto", 1])
    print(TEST)
