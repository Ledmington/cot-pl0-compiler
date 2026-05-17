from symbol_table import Symbol, LabelSymbol

basetypes = ["Int", "Float", "Label", "Struct", "Function"]
qualifiers = ["unsigned"]


class Type(object):
    def __init__(self, name: str, size: int, basetype: str, qualifiers=None):
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

    def getSize(self) -> int:
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
