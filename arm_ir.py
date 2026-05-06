#!/usr/bin/python3

target_info = {
    "available_registers": 10,
}


def CallStat(self) -> str:
    return ""


def BranchStat(self) -> str:
    opcode = "b"
    if self.operator == "eql":
        opcode += "eq"
    elif self.operator == "lss":
        opcode += "lt"
    elif self.operator == "gtr":
        opcode += "gt"
    elif self.operator == "leq":
        opcode += "lt"
    elif self.operator == "geq":
        opcode += "gt"
    elif self.operator == "neq":
        opcode += "ne"
    return "{} {}".format(opcode, self.target.codegen())


def BranchLinkStat(self):
    return "bl {}".format(self.target.codegen())


def EmptyStat(self):
    return ""


def StoreStat(self):
    if self.symbol.storage_class == "global":
        return "ldr r12, ={}\n\tstr {}, [r12]".format(
            self.symbol.codegen(), self.src.codegen()
        )
    return "str {}, [sp, {}]".format(self.src.codegen(), self.symbol.codegen())


def LoadStat(self):
    if self.symbol.value:
        return "mov {}, {}".format(self.dest.codegen(), self.symbol.codegen())
    if self.symbol.storage_class == "global":
        return "ldr r12, ={}\n\tldr {}, [r12]".format(
            self.symbol.codegen(), self.dest.codegen()
        )
    return "ldr {}, [sp, {}]".format(self.dest.codegen(), self.symbol.codegen())


def BinStat(self):
    opcode = "nop"
    if self.operator == "plus":
        opcode = "add"
    elif self.operator == "minus":
        opcode = "sub"
    elif self.operator == "times":
        opcode = "mul"
        if self.src1.register == self.dest.register:
            return "mul r12, {}, {}\n\tmov {}, r12".format(
                self.src1.codegen(), self.src2.codegen(), self.dest.codegen()
            )
    elif self.operator == "slash":
        return "push {{r0,r1}}\n\tmov r12, {}\n\tmov r1, {}\n\tmov r0, r12\n\ttbl soft_sdiv\n\tmov r12, r0\n\t".format(
            self.src1.codegen(),
            self.src2.codegen()
            + "pop {r0,r1}\n\t"
            + "mov {}, r12".format(self.dest.codegen()),
        )

    elif self.operator in ["lss", "gtr", "eql", "neq", "geq", "leq"]:
        opcode = "cmp"
        return "{} {}, {}".format(
            opcode, self.src1.codegen(), self.src2.codegen()
        )
    else:
        raise Exception("operator " + self.operator + " not implemented")
    return "{} {}, {}, {}".format(
        opcode, self.dest.codegen(), self.src1.codegen(), self.src2.codegen()
    )


def UnStat(self):
    opcode = "nop"
    if self.operator == "-":
        opcode = "mvn"
    elif self.operator == "odd":
        return "ands {}, {}, #1".format(self.dest.codegen(), self.src.codegen())
    else:
        raise Exception("operator " + self.operator + " not implemented")
    return "{} {}, {}".format(opcode, self.dest.codegen(), self.src.codegen())


def PrintStat(self):
    if self.symbol.storage_class == "global":
        return (
            "push {r0}\n\tldr r12, ="
            + self.symbol.codegen()
            + "\n\tldr r0, [r12]\n\tbl print\n\tpop {r0}"
        )
    return (
        "push {r0}\n\tldr r0, "
        + self.symbol.codegen()
        + "\n\tbl print\n\tpop {r0}"
    )


def InputStat(self):
    if self.symbol.storage_class == "global":
        return (
            "bl read\n\tldr r12, ="
            + self.symbol.codegen()
            + "\n\tstr r0, [r12]"
        )
    return "bl read\n\tstr r0, [sp, {}]".format(self.symbol.codegen())


def ReturnStat(self):
    if self.size:
        return "add sp, sp, #{}\n\tpop {{pc}}".format(self.size)
    return "pop {pc}"


def FunctionPrologueStat(self):
    if self.size:
        return "push {{lr}}\n\tsub sp, sp, #{}".format(self.size)
    return "push {lr}"


# COMPOUND NODES


def Block(self) -> str:
    res = "\n"

    # If this block has no parent, it means this is block with the main() function,
    # so it needs to define all the global symbols
    if not self.parent:
        res = "\n.section\t.data\n\t.align 8\n"
        for s in self.symtab:
            if s.storage_class == "global":
                res += s.name + ": .long 0\n"
            elif s.value:
                res += s.name + ": .long {}\n".format(s.value)
        res += ".section\t.text\n\t.align\n\t.global main\n\t.type main, %function\n"

    return res


def FunctionDef(self) -> str:
    return "\n\t.global {}\n\t.type {}, %function\n{}: ".format(
        self.symbol.codegen(), self.symbol.codegen(), self.symbol.codegen()
    )
