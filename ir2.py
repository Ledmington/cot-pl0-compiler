#!/usr/bin/python3

import logging
from st import standard_types, getRegister
from lexer import negate_operator


class IRNode(object):
    """Base class for the Intermediate Representation, offers printing and tree traversal facilities"""

    def __init__(self, parent=None, symtab=None, *children):
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

    def replace(self, old, new):
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


class Const(IRNode):
    """Constant objects from the source code"""

    def __init__(self, parent=None, value=0, symb=None, symtab=None):
        if not symb:
            try:
                symb = standard_types["int"](value=int(value))
            except Exception:
                symb = standard_types["float"](value=float(value))
        super(Const, self).__init__(parent, symtab, symb)
        self.mapping = ["value"]

    def lower(self):
        reg = getRegister()
        self.symtab.append(reg)
        node = LoadStat(self.parent, self.value, reg, self.symtab)
        return self.parent.replace(self, node)


class Var(IRNode):
    """Class representing read access to both local and global variables"""

    def __init__(self, parent=None, var=None, symtab=None):
        super(Var, self).__init__(parent, symtab, var)
        self.mapping = ["symbol"]

    def lower(self):
        reg = getRegister()
        self.symtab.append(reg)
        node = LoadStat(self.parent, self.symbol, reg, self.symtab)
        return self.parent.replace(self, node)


# EXPRESSION


class Expr(IRNode):
    """Expression base node, characterised by an operator field"""

    pass

    def getOperator(self):
        return self.operator


class BinExpr(Expr):
    """Binary Expression node, characterised by an operator field and two operands"""

    def __init__(self, parent=None, operator=None, op1=None, op2=None, symtab=None):
        super(BinExpr, self).__init__(parent, symtab, operator, op1, op2)
        self.mapping = ["operator", "op1", "op2"]

    def getOperands(self):
        return self.children[1:]

    def lower(self):
        reg = getRegister()
        self.symtab.append(reg)
        node = BinStat(
            self, self.operator, reg, self.op1.dest, self.op2.dest, self.symtab
        )
        slist = StatList(self.parent, children=[self.op1, self.op2, node])
        return self.parent.replace(self, slist)


class UnExpr(Expr):
    """Unary Expression node, characterised by an operator field and an operand"""

    def __init__(self, parent=None, operator=None, operand=None, symtab=None):
        super(UnExpr, self).__init__(parent, symtab, operand, operand)
        self.mapping = ["operator", "operand"]

    def getOperand(self):
        return self.operand

    def lower(self):
        reg = getRegister()
        self.symtab.append(reg)
        node = BinStat(self, self.operator, reg, self.operand.dest, self.symtab)
        slist = StatList(self.parent, children=[self.operand, node])
        return self.parent.replace(self, slist)


class CallExpr(Expr):
    """Call Expression node, characterised by a target function and a parameters list"""

    def __init__(self, parent=None, function=None, parameters=None, symtab=None):
        children = [function]
        if parameters:
            children += parameters
        super(CallExpr, self).__init__(parent, symtab, *children)
        self.mapping = ["function"]

    def getTargetFunction(self):
        return self.children[0]

    def getParameters(self):
        return self.children[1:]

    def lower(self):
        node = BranchLinkStat(self.parent, None, None, self.function, self.symtab)
        return self.parent.replace(self, node)


class Stat(IRNode):
    """Statement base node; can have a label"""

    def setLabel(self, label):
        self.label = label
        label.value = self  # set target

    def getLabel(self):
        return self.label

    def hasLabel(self):
        try:
            if self.label:
                return True
        except Exception:
            pass
        return False

    def getFunction(self):
        """Find the function to which this statement belong, if any"""
        if not self.parent:
            return "global"
        elif type(self.parent) == FunctionDef:
            return self.parent
        else:
            return self.parent.getFunction()

    def codegen(self):
        """Fallback implementation for codegen"""
        return self.__repr__()


class CallStat(Stat):
    """Procedure call (non-returning)"""

    def __init__(self, parent=None, call_expr=None, symtab=None):
        super(CallStat, self).__init__(parent, symtab, call_expr)
        self.mapping = ["call_expr"]


class IfStat(Stat):
    """Conditional statement node"""

    def __init__(
        self, parent=None, cond=None, thenpart=None, elsepart=None, symtab=None
    ):
        super(IfStat, self).__init__(parent, symtab, cond, thenpart, elsepart)
        self.mapping = ["cond", "thenpart", "elsepart"]

    def lower(self):
        if self.elsepart:
            raise Exception("Lowering of if-else not implemented yet!")
        out_label = standard_types["label"]()
        end = EmptyStat()
        end.setLabel(out_label)
        reg = getRegister()
        self.symtab.append(reg)
        ncond = UnStat(self.parent, "-", reg, self.cond.dest, self.symtab)
        branch = BranchStat(
            self.parent, self.cond.operator, ncond.dest, out_label, self.symtab
        )
        slist = StatList(
            self.parent, children=[self.cond, ncond, branch, thenpart, end]
        )
        return self.parent.replace(self, slist)


class WhileStat(Stat):
    """While loop statement node"""

    def __init__(self, parent=None, cond=None, body=None, symtab=None):
        super(WhileStat, self).__init__(parent, symtab, cond, body)
        self.mapping = ["cond", "body"]

    def lower(self):
        out_label = standard_types["label"]()
        back_label = standard_types["label"]()
        end = EmptyStat()
        end.setLabel(out_label)
        reg = getRegister()
        self.symtab.append(reg)
        branch_out = BranchStat(
            self.parent,
            negate_operator(self.cond.operator),
            reg,
            out_label,
            self.symtab,
        )
        branch_back = BranchStat(self.parent, None, None, back_label, self.symtab)
        self.cond.setLabel(back_label)
        logging.debug("{} attached to {}".format(self.cond.getLabel(), self.cond))
        slist = StatList(
            self.parent, children=[self.cond, branch_out, self.body, branch_back, end]
        )
        return self.parent.replace(self, slist)


class AssignStat(Stat):
    """Assignment statement node (writes to a variable the value of an expression)"""

    def __init__(self, parent=None, target=None, expr=None, symtab=None):
        super(AssignStat, self).__init__(parent, symtab, target, expr)
        self.mapping = ["target", "expr"]

    def lower(self):
        node = StoreStat(self.parent, self.target, self.expr.dest, self.symtab)
        slist = StatList(self.parent, children=[self.expr, node])
        return self.parent.replace(self, slist)


# LOW LEVEL REPRESENTATION


class BranchStat(Stat):
    """Branch statement node (low level)"""

    def __init__(self, parent=None, operator=None, src=None, target=None, symtab=None):
        super(BranchStat, self).__init__(parent, symtab, operator, src, target)
        self.mapping = ["operator", "src", "target"]

    def is_unconditional(self):
        return self.operator


class BranchLinkStat(BranchStat):
    """Branch and link statement node"""

    pass


class EmptyStat(Stat):
    """NOP-like statement, useful to attach a label at the end of a code block without need to know what is next"""

    pass


class StoreStat(Stat):
    """Store-to-memory statement node"""

    def __init__(self, parent=None, symbol=None, src=None, symtab=None):
        super(StoreStat, self).__init__(parent, symtab, symbol, src)
        self.mapping = ["symbol", "src"]


class LoadStat(Stat):
    """Load-from-memory statement node"""

    def __init__(self, parent=None, symbol=None, dest=None, symtab=None):
        super(LoadStat, self).__init__(parent, symtab, dest, symbol)
        self.mapping = ["dest", "symbol"]


class BinStat(Stat):
    """Binary statement node (three operand instruction R1 = R2 op R3)"""

    def __init__(
        self, parent=None, operator=None, dest=None, src1=None, src2=None, symtab=None
    ):
        super(BinStat, self).__init__(parent, symtab, operator, dest, src1, src2)
        self.mapping = ["operator", "dest", "src1", "src2"]


class UnStat(Stat):
    """Unary statement node (two operand instruction R1 = op R2)"""

    def __init__(self, parent=None, operator=None, dest=None, src=None, symtab=None):
        super(UnStat, self).__init__(parent, symtab, operator, dest, src)
        self.mapping = ["operator", "dest", "src"]


class PrintStat(Stat):
    """Built-in function to print variable value"""

    def __init__(self, parent=None, symbol=None, symtab=None):
        super(PrintStat, self).__init__(parent, symtab, symbol)
        self.mapping = ["symbol"]


class ReturnStat(Stat):
    """Return statement node"""

    pass


class FunctionPrologueStat(Stat):
    """Return statement node"""

    pass


# COMPOUND NODES


class StatList(Stat):
    """Statement List: allows to define sequences of instructions; used both in high and low level representation with the same meaning; offers facilities for flattening nested StatLists"""

    def __init__(self, parent=None, children=None, symtab=None):
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
        print(f"elem = '{elem}'")
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
        if type(self.parent) == StatList:
            logging.debug("Flattening {} into {}".format(id(self), id(self.parent)))
            for c in self.children:
                c.parent = self.parent
            i = self.parent.children.index(self)
            self.parent.children = (
                self.parent.children[:i] + self.children + self.parent.children[i + 1 :]
            )
            return True
        else:
            logging.debug(
                "Not flattening {} into {} of type {}".format(
                    id(self), id(self.parent), type(self.parent)
                )
            )
            return False


class Block(Stat):
    """Scope block node"""

    def __init__(self, parent=None, gl_sym=None, lc_sym=None, defs=None, body=None):
        lc_sym.setParent(gl_sym)
        lc_sym.setScopeBlock(self)
        super(Block, self).__init__(parent, lc_sym, defs, body)
        self.mapping = ["defs", "body"]

    def lower(self):
        if not self.parent:  # Global Block
            new_pr = FunctionPrologueStat()
            new_ep = ReturnStat()
            stlist = StatList(
                self, children=[new_pr, self.body, new_ep], symtab=self.body.symtab
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

    def navigate(self, action, post=False):
        """Redefine navigate to force main to be generated before other functions"""
        if not post:
            action(self)
        self.body.navigate(action, post)
        self.defs.navigate(action, post)
        if post:
            action(self)


# DEFINITIONS


class Definition(IRNode):
    """Definitions base node"""

    def __init__(self, parent=None, symbol=None):
        super(Definition, self).__init__(parent, None, symbol)
        self.mapping = ["symbol"]


class FunctionDef(Definition):
    """Function Definition node"""

    def __init__(self, parent=None, symbol=None, body=None):
        super(Definition, self).__init__(parent, None, symbol, body)
        self.mapping = ["symbol", "body"]

    def getGlobalSymbols(self):
        return self.body.global_symtab.exclude(
            [standard_types["function"], standard_types["label"]]
        )

    def lower(self):
        new_pr = FunctionPrologueStat()
        new_ep = ReturnStat()
        slist = StatList(self, children=[new_pr, self.body, new_ep])
        self.body = slist


class DefinitionList(IRNode):
    """List of definitions"""

    def __init__(self, parent=None, children=[]):
        super(DefinitionList, self).__init__(parent, None, *children)

    def append(self, elem):
        elem.parent = self
        self.children.append(elem)


def subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in subclasses(c)]
    )


def setup(target):
    func = lambda self: ""
    import importlib
    from types import MethodType

    try:
        the_target = importlib.import_module(target)
    except ImportError:
        func = lambda self: repr(type(self)) + " " + repr(id(self))
    for the_class in subclasses(IRNode):
        try:
            if issubclass(the_class, IRNode):
                setattr(the_class, "codegen", eval("the_target." + the_class.__name__))
        except Exception:
            setattr(the_class, "codegen", func)

    return the_target.target_info


if __name__ == "__main__":
    TEST = CallExpr(function="pippo", parameters=["pluto", 1])
    print(TEST)
