from ir2 import FunctionDefinition
from ir_node import IRNode


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
