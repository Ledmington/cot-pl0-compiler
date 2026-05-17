from __future__ import annotations

import logging
from typing import Callable, Optional, Any

from printer import Printer
from symbol_table import SymbolTable


class IRNode(object):
    """Base class for the Intermediate Representation, offers printing and tree traversal facilities"""

    parent: Optional[IRNode]
    symtab: Optional[SymbolTable]
    mapping: list[Any]
    children: list[IRNode]

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

    def __repr__(self) -> str:
        return self.to_string(Printer())

    def to_string(self, printer: Printer) -> str:
        try:
            printer += self.label.codegen() + " : "
        except Exception:
            pass

        printer += repr(type(self)) + " " + repr(id(self)) + " {"

        for c in self.children:
            printer += str(repr(c)) + "\n"

        return printer.__repr__()

    def __getattr__(self, attr):
        return self.children[self.mapping.index(attr)]

    def __setattr__(self, attr: str, value) -> None:
        has_mapping = True if "mapping" in self.__dict__ else False
        if attr == "mapping" or not has_mapping or attr not in self.mapping:
            object.__setattr__(self, attr, value)
            return
        self.children[self.mapping.index(attr)] = value

    def navigate(
        self, action: Callable[[IRNode], None], post: bool = False
    ) -> None:
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

    def collect_uses(self) -> list[Any]:
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
