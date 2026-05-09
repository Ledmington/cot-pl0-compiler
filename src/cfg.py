__doc__ = """Control Flow Graph implementation
Includes cfg construction and liveness analysis."""

import logging
from functools import reduce
from pathlib import Path

from definitions import FunctionDefinition
from statements import BranchStatement, CallStatement, StatementList
from support import get_node_list

logger = logging.getLogger("cfg")


class BasicBlock(object):
    def __init__(self, next=None, instrs=None, labels=None):
        """Structure:
        Zero, one (next) or two (next, target_bb) successors
        Keeps information on labels
        """
        if instrs is None:
            instrs = []
        self.next = next
        self.instrs = instrs

        try:
            self.target = self.instrs[-1].target
        except Exception:
            self.target = None

        if labels:
            self.labels = labels
        else:
            self.labels = []
        self.target_bb = None

        self.live_in = set([])
        self.live_out = set([])
        self.kill = set([])  # assigned
        self.gen = set([])  # use before assign
        for i in instrs:
            uses = set(i.collect_uses()) - {None}
            uses.difference_update(self.kill)
            self.gen.update(uses)
            try:
                self.kill.add(i.dest)
            except Exception:
                pass

        # Total number of registers needed
        self.total_vars_used = len(self.gen.union(self.kill))

        live_in = [self.live_out]
        for i in reversed(self.instrs):
            try:
                kill = {i.dest}
            except Exception:
                kill = set([])
            gen = set(i.collect_uses()) - kill - {None}
            live_in.append(gen.union(live_in[-1] - kill))
        live_in.pop(-1)
        for i in self.instrs:
            i.live_out = live_in.pop(-1)

    def __repr__(self):
        """Print in graphviz dot format"""
        instrs = repr(self.labels) + "\\n" if len(self.labels) else ""
        """live_in=[self.live_out]
        for i in reversed(self.instrs) :
            try: kill=set([i.dest])
            except Exception, e: kill=set([])
            gen = set(i.collect_uses())-kill-set([None])
            live_in.append(gen.union(live_in[-1] - kill))
        live_in.pop(-1)"""
        for i in self.instrs:
            try:
                text = i.codegen()
            except ValueError:
                text = type(i)
            instrs += repr(text) + "\n { " + repr(i.live_out) + " }\n"
        res = (
            repr(id(self))
            + ' [label="BB'
            + repr(id(self))
            + "{\\n"
            + instrs
            + '}"];\n'
        )
        if self.next:
            res += (
                repr(id(self))
                + " -> "
                + repr(id(self.next))
                + ' [label="'
                + repr(self.next.live_in)
                + '"];\n'
            )
        if self.target_bb:
            res += (
                repr(id(self))
                + " -> "
                + repr(id(self.target_bb))
                + ' [style=dashed,label="'
                + repr(self.target_bb.live_in)
                + '"];\n'
            )
        if not (self.next or self.target_bb):
            res += (
                repr(id(self))
                + " -> "
                + "exit"
                + repr(id(self.get_function()))
                + ' [label="'
                + repr(self.live_out)
                + '"];\n'
            )
        return res

    def succ(self):
        return [s for s in [self.target_bb, self.next] if s]

    def liveness_iteration(self):
        """Compute live_in and live_out approximation
        Returns: check of fixed point"""
        lin = len(self.live_in)
        lout = len(self.live_out)

        if self.next or self.target_bb:
            self.live_out = reduce(
                lambda x, y: x.union(y),
                [s.live_in for s in self.succ()],
                set([]),
            )

        self.live_in = self.gen.union(self.live_out - self.kill)

        # We want to do another iteration if the sizes of live_in and live_out have changed
        return not (lin == len(self.live_in) and lout == len(self.live_out))

    def remove_useless_next(self):
        """Check if unconditional branch, in that case remove next"""
        try:
            if self.instrs[-1].is_unconditional():
                self.next = None
        except Exception:
            pass

    def get_function(self):
        return self.instrs[0].get_function()


def stat_list_to_bb(sl):
    """Support function for converting AST StatList to BBs"""
    bbs = []
    newbb = []
    labels = []
    for n in sl.children:
        try:
            label = n.get_label()
            if label:
                if len(newbb):
                    bb = BasicBlock(None, newbb, labels)
                    newbb = []
                    if len(bbs):
                        bbs[-1].next = bb
                    bbs.append(bb)
                    labels = [label]
                else:
                    labels.append(label)
        except Exception:
            pass

        newbb.append(n)

        if isinstance(n, BranchStatement) or isinstance(n, CallStatement):
            bb = BasicBlock(None, newbb, labels)
            newbb = []
            if len(bbs):
                bbs[-1].next = bb
            bbs.append(bb)
            labels = []

    if len(newbb) or len(labels):
        bb = BasicBlock(None, newbb, labels)
        if len(bbs):
            bbs[-1].next = bb
        bbs.append(bb)
    return bbs


class CFG(list):
    """Control Flow Graph representation"""

    def __init__(self, root):
        super().__init__()

        stat_lists = [
            n for n in get_node_list(root) if isinstance(n, StatementList)
        ]
        self += sum([stat_list_to_bb(sl) for sl in stat_lists], [])
        for bb in self:
            if bb.target:
                bb.target_bb = self.find_target_bb(bb.target)
            bb.remove_useless_next()

    def heads(self):
        """Get bbs that are only reached via function call or global entry point"""
        defs = []
        for bb1 in self:
            head = True
            for bb2 in self:
                if bb2.next == bb1 or bb2.target_bb == bb1:
                    head = False
                    break
            if head:
                defs.append(bb1)

        print(" ### DEFS ### ")
        print(defs)
        print(" ### DEFS ### ")

        res = {}
        for bb in defs:
            first = bb.instrs[0]
            parent = first.parent
            while parent is not None and isinstance(parent, FunctionDefinition):
                parent = parent.parent
            if not parent:
                res["global"] = bb
            else:
                res[parent] = bb

        print(" ### RES ### ")
        print(res)
        print(" ### RES ### ")

        return res

    def print_cfg_to_dot(self, filename: Path) -> None:
        """Print the CFG in graphviz dot to file"""
        print("writing to '{filename}'".format(filename=filename))
        with open(filename, "w") as f:
            f.write("digraph G {\n")
            for n in self:
                f.write(repr(n))
            h = self.heads()

            print(" ### HEADS ###")
            print(h)
            print(" ### HEADS ###")

            for p in h:
                bb = h[p]
                if p == "global":
                    f.write("main [shape=box];\n")
                    f.write(
                        "main -> "
                        + repr(id(bb))
                        + ' [label="'
                        + repr(bb.live_in)
                        + '"];\n'
                    )
                else:
                    f.write(p.symbol.name + " [shape=box];\n")
                    f.write(
                        p.symbol.name
                        + " -> "
                        + repr(id(bb))
                        + ' [label="'
                        + repr(bb.live_in)
                        + '"];\n'
                    )
            f.write("}\n")

    def print_liveness(self):
        print("Liveness sets")
        for bb in self:
            print(bb)
            print("gen:", bb.gen)
            print("kill:", bb.kill)
            print("live_in:", bb.live_in)
            print("live_out:", bb.live_out)

    def find_target_bb(self, label):
        """Return the BB that contains a given label;
        Support function for creating/exploring the CFG"""
        for bb in self:
            if label in bb.labels:
                return bb
        raise Exception(repr(label) + " not found in any BB!")

    def liveness(self):
        """Standard live variable analysis"""
        out = []
        for bb in self:
            out.append(bb.liveness_iteration())
        while sum(out):
            out = []
            for bb in self:
                out.append(bb.liveness_iteration())
        return

    def reg_alloc(self, n=8):
        from itertools import permutations

        ig = []
        regs = []

        for bb in self:
            for i in bb.instrs:
                ig += permutations(i.live_out, 2)
                regs += i.live_out

        ig = set(ig)
        regs = set(regs)
        logger.debug("Registers: {}".format(regs))
        logger.debug("Interference Graph: {}".format(ig))
        registers = set(range(8))

        def getInterf(r, ig):
            return set(
                [
                    x[1].register
                    for x in ig
                    if x[0] == r and x[1].register is not None
                ]
            )

        for r in regs:
            i = getInterf(r, ig)
            available = list(registers - i)
            sorted(available)  # FIXME: useless?
            r.register = available[
                0
            ]  # TODO: add spilling to prevent an exception to occur here
