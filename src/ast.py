from types import Type


class ASTNode(object):
    """Common type for all nodes in the AST"""

    pass


class VariableDeclarationNode(ASTNode):
    """The AST node representing a variable declaration"""

    _name: str
    _type: Type

    def __init__(self, name: str, type: Type):
        self._name = name
        self._type = type


class FunctionDeclarationNode(ASTNode):
    """The AST node representing a function declaration"""

    pass


class ProgramNode(ASTNode):
    """The AST node representing a whole program"""

    _variables_declarations: list[VariableDeclarationNode]
    _function_declarations: list[FunctionDeclarationNode]

    def __init__(
        self,
        variable_declarations: list[VariableDeclarationNode],
        function_declarations: list[FunctionDeclarationNode],
    ):
        self._variable_declarations = variable_declarations
        self._function_declarations = function_declarations
