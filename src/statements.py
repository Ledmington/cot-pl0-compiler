import logging
from typing import Optional

from ir2 import FunctionDefinition
from ir_node import IRNode
from lexer import Lexer
from st import SymbolTable, getRegister, standard_types


class Statement(IRNode):
    """Statement base node; can have a label"""

    def set_label(self, label: str) -> None:
        self.label = label
        label.value = self  # set target

    def getLabel(self) -> str:
        return self.label

    def hasLabel(self) -> bool:
        try:
            if self.label:
                return True
        except Exception:
            pass
        return False

    def getFunction(self) -> str | FunctionDefinition:
        """Find the function to which this statement belongs, if any"""
        if not self.parent:
            return "global"
        elif isinstance(self.parent, FunctionDefinition):
            return self.parent
        else:
            return self.parent.getFunction()

    def codegen(self) -> str:
        """Fallback implementation for codegen"""
        return self.__repr__()


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

    def lower(self) -> bool:
        if self.elsepart:
            raise Exception("Lowering of if-else not implemented yet!")
        out_label = standard_types["label"]()
        end = EmptyStatement()
        end.set_label(out_label)
        reg = getRegister()
        self.symtab.append(reg)
        ncond = UnaryStatement(
            self.parent, "-", reg, self.cond.dest, self.symtab
        )
        branch = BranchStatement(
            self.parent, self.cond.operator, ncond.dest, out_label, self.symtab
        )
        slist = StatementList(
            self.parent,
            children=[
                self.cond,
                ncond,
                branch,
                # thenpart,
                end,
            ],
        )
        return self.parent.replace(self, slist)


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

    def lower(self) -> bool:
        out_label = standard_types["label"]()
        back_label = standard_types["label"]()
        end = EmptyStatement()
        end.set_label(out_label)
        reg = getRegister()
        self.symtab.append(reg)
        branch_out = BranchStatement(
            self.parent,
            Lexer.negate_operator(self.cond.operator),
            reg,
            out_label,
            self.symtab,
        )
        branch_back = BranchStatement(
            self.parent, None, None, back_label, self.symtab
        )
        self.cond.set_label(back_label)
        logging.debug(
            "{} attached to {}".format(self.cond.getLabel(), self.cond)
        )
        slist = StatementList(
            self.parent,
            children=[self.cond, branch_out, self.body, branch_back, end],
        )
        return self.parent.replace(self, slist)


class AssignStatement(Statement):
    """Assignment statement node (writes to a variable the value of an expression)"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        target=None,
        expr=None,
        symtab: Optional[SymbolTable] = None,
    ):
        super(AssignStatement, self).__init__(parent, symtab, target, expr)
        self.mapping = ["target", "expr"]

    def lower(self) -> bool:
        node = StoreStatement(
            self.parent, self.target, self.expr.dest, self.symtab
        )
        slist = StatementList(self.parent, children=[self.expr, node])
        return self.parent.replace(self, slist)


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
        logging.debug("StatList : new {}".format(id(self)))
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
        logging.debug(
            "StatList: inserting {} of type {} into {}".format(
                id(elem), type(elem), id(self)
            )
        )
        self.children.insert(index, elem)

    def append(self, elem):
        elem.parent = self
        logging.debug(
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

    def print_content(self):
        logging.debug("StatList {} : [".format(id(self)))
        for n in self.children:
            logging.debug("{} ".format(id(n)))
        logging.debug("]")

    def set_label(self, label):
        self.children[0].set_label(label)

    def flatten(self):
        """Remove nested StatLists"""
        if isinstance(self.parent, StatementList):
            logging.debug(
                "Flattening {} into {}".format(id(self), id(self.parent))
            )
            for c in self.children:
                c.parent = self.parent
            i = self.parent.children.index(self)
            self.parent.children = (
                self.parent.children[:i]
                + self.children
                + self.parent.children[i + 1 :]
            )
            return True
        else:
            logging.debug(
                "Not flattening {} into {} of type {}".format(
                    id(self), id(self.parent), type(self.parent)
                )
            )
            return False
