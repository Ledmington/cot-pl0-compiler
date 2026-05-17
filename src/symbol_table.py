from __future__ import annotations

import logging
from typing import Optional

from printer import Printer
from types import Type

logger = logging.getLogger("symtab")


class Symbol(object):
    def __init__(self, name: str, stype: Type, value=None):
        # NOTE: not all the following values are always meaningful
        # For example, offset is needed only for values in memory
        self.name = name
        self.stype = stype
        self.value = value  # if not None, it is a constant
        self.storage_class = None
        if value is not None:
            self.storage_class = "const"
        self.register = None
        self.offset = 0

    def __repr__(self) -> str:
        printer = Printer()
        self.to_string(printer)
        return printer.__repr__()

    def to_string(self, printer: Printer = Printer()) -> None:
        printer += (
            self.stype.name
            + " "
            + self.name
            + " "
            + repr(self.value)
            + (" const" if self.value else "")
            + " "
            + (self.storage_class if self.storage_class else "")
        )

    def codegen(self) -> str:
        return self.stype.name + " " + self.name


class LabelSymbol(Symbol):
    def __repr__(self) -> str:
        return "label " + self.name


class SymbolTable(list):
    def find(self, name: str) -> Optional[Symbol]:
        logger.debug("Looking up {}".format(name))

        for s in self:
            if s.name == name:
                return s

        logger.debug("Looking up in parent")

        try:
            return self.parent.find(name)
        except Exception:
            pass

        logger.debug("Looking up failed!")

        return None

    def __repr__(self) -> str:
        res = "SymbolTable: {\n"
        for s in self:
            res += repr(s) + "\n"
        res += "}\n"
        return res

    def exclude(self, barred_types: list[Type]) -> list[Type]:
        return [symb for symb in self if symb.stype not in barred_types]

    def set_parent(self, parent: SymbolTable) -> None:
        self.parent = parent

    def get_parent(self) -> Optional[SymbolTable]:
        try:
            return self.parent
        except AttributeError:
            return None


def getRegister(stype: str = "int") -> Symbol:
    reg = standard_types[stype]()
    reg.storage_class = "register"
    return reg
