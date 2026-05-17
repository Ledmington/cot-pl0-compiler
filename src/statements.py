import logging
from typing import Optional

from definitions import FunctionDefinition
from ir_node import IRNode
from printer import Printer
from symbol_table import SymbolTable

logger = logging.getLogger("statements")


class Statement(IRNode):
    """Statement base node; can have a label"""

    def set_label(self, label: str) -> None:
        self.label = label
        label.value = self  # set target

    def get_label(self) -> str:
        return self.label

    def has_label(self) -> bool:
        try:
            if self.label:
                return True
        except Exception:
            pass
        return False

    def get_function(self) -> str | FunctionDefinition:
        """Find the function to which this statement belongs, if any"""
        if not self.parent:
            return "global"
        elif isinstance(self.parent, FunctionDefinition):
            return self.parent
        else:
            return self.parent.get_function()


class CallStatement(Statement):
    """Procedure call (non-returning)"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        call_expr=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(CallStatement, self).__init__(parent, symtab, call_expr)
        self.mapping = ["call_expr"]


class IfStatement(Statement):
    """Conditional statement node"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        cond=None,
        thenpart=None,
        elsepart=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(IfStatement, self).__init__(
            parent, symtab, cond, thenpart, elsepart
        )
        self.mapping = ["cond", "thenpart", "elsepart"]


class WhileStatement(Statement):
    """While loop statement node"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        cond=None,
        body=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(WhileStatement, self).__init__(parent, symtab, cond, body)
        self.mapping = ["cond", "body"]


class AssignmentStatement(Statement):
    """Assignment statement node (writes to a variable the value of an expression)"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        target=None,
        expr=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(AssignmentStatement, self).__init__(parent, symtab, target, expr)
        self.mapping = ["target", "expr"]

    # why?
    def __iter__(self):
        yield self

    def __repr__(self) -> str:
        return self.to_string()

    def to_string(self, printer: Printer = Printer()) -> str:
        printer += "AssignmentStatement {\n"
        printer.indent(1)
        printer += (
            "target: "
            + (self.target.to_string(printer) if self.target else "None")
            + "\n"
        )
        printer += "expr: " + self.expr.to_string(printer) + "\n"
        printer.indent(-1)
        printer += "}"
        return printer.__repr__()


# LOW LEVEL REPRESENTATION


class BranchStatement(Statement):
    """Branch statement node (low level)"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        operator=None,
        src=None,
        target=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(BranchStatement, self).__init__(
            parent, symtab, operator, src, target
        )
        self.mapping = ["operator", "src", "target"]

    def is_unconditional(self):
        return self.operator


class BranchLinkStatement(BranchStatement):
    """Branch and link statement node"""

    pass


class EmptyStatement(Statement):
    """NOP-like statement, useful to attach a label at the end of a code block without need to know what is next"""

    pass


class StoreStatement(Statement):
    """Store-to-memory statement node"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        symbol=None,
        src=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(StoreStatement, self).__init__(parent, symtab, symbol, src)
        self.mapping = ["symbol", "src"]


class LoadStatement(Statement):
    """Load-from-memory statement node"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        symbol=None,
        dest=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(LoadStatement, self).__init__(parent, symtab, dest, symbol)
        self.mapping = ["dest", "symbol"]


class BinaryStatement(Statement):
    """Binary statement node (three operand instruction R1 = R2 op R3)"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        operator=None,
        dest=None,
        src1=None,
        src2=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(BinaryStatement, self).__init__(
            parent, symtab, operator, dest, src1, src2
        )
        self.mapping = ["operator", "dest", "src1", "src2"]


class UnaryStatement(Statement):
    """Unary statement node (two operand instruction R1 = op R2)"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        operator=None,
        dest=None,
        src=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(UnaryStatement, self).__init__(
            parent, symtab, operator, dest, src
        )
        self.mapping = ["operator", "dest", "src"]


class PrintStatement(Statement):
    """Built-in function to print variable value"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        symbol=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(PrintStatement, self).__init__(parent, symtab, symbol)
        self.mapping = ["symbol"]


class ReturnStatement(Statement):
    """Return statement node"""

    pass


class FunctionPrologueStatement(Statement):
    """Return statement node"""

    pass


# COMPOUND NODES


class StatementList(Statement):
    """Statement List: allows to define sequences of instructions; used both in high and low level representation with the same meaning; offers facilities for flattening nested StatLists"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        children: list[Statement] = None,
        symtab: Optional[SymbolTable] = None,
    ):
        super().__init__(parent, symtab, children)
        logger.debug("StatList : new {}".format(id(self)))
        self.parent = parent
        if children:
            self.children = children[:]
            for c in self.children:
                c.parent = self
        else:
            self.children = []
        self.symtab = symtab

    def insert(self, index, elem):
        elem.parent = self
        logger.debug(
            "StatList: inserting {} of type {} into {}".format(
                id(elem), type(elem), id(self)
            )
        )
        self.children.insert(index, elem)

    def append(self, elem):
        elem.parent = self
        logger.debug(
            "StatList: appending {} of type {} to {}".format(
                id(elem), type(elem), id(self)
            )
        )
        self.children.append(elem)

    def __getattr__(self, attr):
        if attr == "dest":
            return self.children[-1].dest
        if attr == "operator":
            return self.children[-1].operator
        return None

    def __repr__(self) -> str:
        return self.to_string()

    def to_string(self, printer: Printer = Printer()) -> str:
        printer += "StatementList {\n"
        printer.indent(1)
        for stmt in self.children:
            printer += stmt.to_string(printer)
        printer.indent(-1)
        printer += "}"
        return printer.__repr__()

    def set_label(self, label):
        self.children[0].set_label(label)

    def __iter__(self):
        for stmt in self.children:
            yield stmt
