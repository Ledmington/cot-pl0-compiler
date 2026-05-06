from __future__ import annotations

import importlib
import logging
from typing import Optional

from lexer import Lexer
from st import SymbolTable, getRegister, standard_types


class IRNode(object):
    """Base class for the Intermediate Representation, offers printing and tree traversal facilities"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        symtab: Optional[SymbolTable] = None,
        *children,
    ):
        self.parent = parent
        self.symtab = symtab
        self.mapping = []
        self.children = list(children) if children else []
        for c in self.children:
            try:
                c.parent = self
            except AttributeError:
                pass

    def __repr__(self):
        line = ""
        try:
            line = self.label.codegen() + " : "
        except Exception:
            pass
        lines = [line + repr(type(self)) + " " + repr(id(self)) + " {"]
        for c in self.children:
            lines += "{}".format(repr(c)).split("\n")
        return "\n\t".join(lines) + "\n}"

    def __getattr__(self, attr):
        return self.children[self.mapping.index(attr)]

    def __setattr__(self, attr, value):
        has_mapping = True if "mapping" in self.__dict__ else False
        if attr == "mapping" or not has_mapping or attr not in self.mapping:
            object.__setattr__(self, attr, value)
            return
        self.children[self.mapping.index(attr)] = value

    def navigate(self, action, post=False):
        if not post:
            action(self)
        for c in self.children:
            try:
                c.navigate(action, post)
            except Exception:
                pass
        if post:
            action(self)

    def replace(self, old, new) -> bool:
        try:
            self.children[self.children.index(old)] = new
            return True
        except Exception as e:
            logging.debug("Exception while replacing {}".format(e))
            return False

    def collect_uses(self):
        uses = []
        try:
            uses.append(self.src)
        except Exception:
            pass
        try:
            uses.append(self.src1)
        except Exception:
            pass
        try:
            uses.append(self.src2)
        except Exception:
            pass
        logging.debug("Uses of {}: {}".format(self, uses))
        return uses


# CONST & VAR


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


class Statement(IRNode):
    """Statement base node; can have a label"""

    def setLabel(self, label: str) -> None:
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
        """Find the function to which this statement belong, if any"""
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
        end.setLabel(out_label)
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
        end.setLabel(out_label)
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
        self.cond.setLabel(back_label)
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


class BranchLinkStat(BranchStatement):
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

    def setLabel(self, label):
        self.children[0].setLabel(label)

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


class Block(Statement):
    """Scope block node"""

    def __init__(
        self,
        parent: Optional[IRNode] = None,
        gl_sym: SymbolTable = None,
        lc_sym: SymbolTable = None,
        defs=None,
        body=None,
    ):
        lc_sym.setParent(gl_sym)
        lc_sym.setScopeBlock(self)
        super(Block, self).__init__(parent, lc_sym, defs, body)
        self.mapping = ["defs", "body"]

    def lower(self) -> None:
        if not self.parent:  # Global Block
            new_pr = FunctionPrologueStatement()
            new_ep = ReturnStatement()
            stlist = StatementList(
                self,
                children=[new_pr, self.body, new_ep],
                symtab=self.body.symtab,
            )
            self.body = stlist
            self.body.setLabel(standard_types["label"]("main"))

    def dataLayout(self):
        if not self.parent:
            for s in self.symtab:
                if not s.storage_class and s.stype not in [
                    standard_types["label"],
                    standard_types["function"],
                ]:
                    # anything that has not a storage class and is not a label or a function, we place in the global namespace
                    s.storage_class = "global"
        # auto layout
        else:
            off = 0
            for s in self.symtab:
                if not s.storage_class and s.stype not in [
                    standard_types["label"],
                    standard_types["function"],
                ]:
                    s.storage_class = "auto"
                    off += s.stype.size / 8
                    s.offset = off
            self.symtab.size = off
        return True

    def navigate(self, action, post: bool = False) -> None:
        """Redefine navigate to force main to be generated before other functions"""
        if not post:
            action(self)
        self.body.navigate(action, post)
        self.defs.navigate(action, post)
        if post:
            action(self)


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

    def append(self, elem):
        elem.parent = self
        self.children.append(elem)


def subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in subclasses(c)]
    )


def setup(target):
    def func(self):
        return ""

    try:
        the_target = importlib.import_module(target)
    except ImportError:

        def func(self):
            return repr(type(self)) + " " + repr(id(self))

    for the_class in subclasses(IRNode):
        try:
            if issubclass(the_class, IRNode):
                setattr(
                    the_class,
                    "codegen",
                    eval("the_target." + the_class.__name__),
                )
        except Exception:
            setattr(the_class, "codegen", func)

    return the_target.target_info


if __name__ == "__main__":
    TEST = CallExpression(function="pippo", parameters=["pluto", 1])
    print(TEST)
