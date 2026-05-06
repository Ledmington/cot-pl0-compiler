#!/usr/bin/python3

import logging

# SYMBOLS AND TYPES
basetypes = ["Int", "Float", "Label", "Struct", "Function"]
qualifiers = ["unsigned"]


class Type(object):
    def __init__(self, name, size, basetype, qualifiers=None):
        if qualifiers is None:
            qualifiers = []
        self.name = name
        self.size = size
        self.basetype = basetype
        self.qual_list = qualifiers
        self.ids = 0

    def __call__(self, value=None):
        self.ids += 1
        return Symbol(name=self.name + repr(self.ids), stype=self, value=value)


class ArrayType(Type):
    def __init__(self, name, size, basetype):
        super(ArrayType, self).__init__(name, size, basetype)


class StructType(Type):
    def __init__(self, name, size, fields):
        super(StructType, self).__init__(
            name, sum([f.size for f in fields]), "Struct"
        )
        self.fields = fields

    def getSize(self):
        return sum([f.size for f in self.fields])


class LabelType(Type):
    def __init__(self):
        super(LabelType, self).__init__("label", 0, "Label")

    def __call__(self, value=None):
        self.ids += 1
        if value == "main":
            return LabelSymbol(name="main", stype=self, value=value)
        return LabelSymbol(
            name=self.name + repr(self.ids), stype=self, value=value
        )


class FunctionType(Type):
    def __init__(self):
        super(FunctionType, self).__init__("function", 0, "Function")


standard_types = {
    "int": Type("int", 32, "Int"),
    "short": Type("short", 16, "Int"),
    "char": Type("char", 8, "Int"),
    "uchar": Type("uchar", 8, "Int", ["unsigned"]),
    "uint": Type("uint", 32, "Int", ["unsigned"]),
    "ushort": Type("ushort", 16, "Int", ["unsigned"]),
    "float": Type("float", 32, "Float"),
    "label": LabelType(),
    "function": FunctionType(),
}


class Symbol(object):
    def __init__(self, name, stype, value=None):
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

    def codegen(self):
        if self.storage_class == "const":
            return "#{}".format(self.value)
        if self.storage_class == "global":
            return self.name
        if self.storage_class == "register" and self.register is not None:
            return "r{}".format(self.register)
        if self.storage_class == "auto":
            return "#{}".format(
                self.offset - 4
            )  # bit of a hack (this 4 should be taken from a config file, but it's fine for this toy compiler)
        return self.name

    def __repr__(self):
        res = self.stype.name + " " + self.name
        res += (" " + repr(self.value) + " const" if self.value else "") + " "
        res += self.storage_class if self.storage_class else ""
        return res


class LabelSymbol(Symbol):
    def codegen(self):
        return self.name

    def __repr__(self):
        return "label " + self.name


class SymbolTable(list):
    def find(self, name):
        logging.debug("Looking up {}".format(name))
        for s in self:
            if s.name == name:
                return s
        logging.debug("Looking up in parent")
        try:
            return self.parent.find(name)
        except Exception:
            pass
        logging.debug("Looking up failed!")
        return None

    def __repr__(self):
        res = "SymbolTable:\n"
        for s in self:
            res += repr(s) + "\n"
        return res

    def exclude(self, barred_types):
        return [symb for symb in self if symb.stype not in barred_types]

    def setParent(self, parent):
        self.parent = parent

    def getParent(self):
        try:
            return self.parent
        except AttributeError:
            return None

    def setScopeBlock(self, scope):
        self.block = scope

    def getScopeBlock(self):
        return self.block


def getRegister(stype="int"):
    reg = standard_types[stype]()
    reg.storage_class = "register"
    return reg


if __name__ == "__main__":
    for i in range(10):
        print(getRegister())
