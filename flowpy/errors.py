import ast
from .arguments import Format

class FlowVar:
    """
    FlowVar is a wrapper class for a variable name and its labels.
    """

    def __init__(self, name, labels):
        self.name = name
        self.labels = labels

    def __str__(self):
        return f"{Format.BOLD}{self.name}{Format.END} : {Format.GREY}{self.labels if self.labels is not None else 'untracked'}{Format.END}"


# Purpose: Defines the base class for all flow faults.
class FlowError(Exception):
    """
    Base class for defining all flow error.
    Could be raised but also treated as a regular object.
    """

    def __init__(
        self,
        node: ast.AST=None,
        var_to=None,
        info="",
    ) -> None:
        """
        Initialise a flow error.
        """
        self.node: ast.AST = node
        self.line: int = None if node is None else node.lineno
        self.var_to: FlowVar = var_to
        self.info: list = info

    def get_code(self):
        """
        Returns the code that caused the error.
        """
        return ast.unparse(self.node)

class ImplicitFlowError(FlowError):
    """
    ImplicitFlowError is a flow error that occurs when a variable is assigned
    to when PC is not a subset of the variable's labels.
    """

    def __init__(
        self, node: ast.AST, pc: set = None, var_to: FlowVar = None, info: str = ""
    ) -> None:
        super().__init__(node, var_to, info)
        self.pc = pc

    def __str__(self) -> str:
        message = [
            f"{Format.BOLD+Format.ORANGE}Implicit Flow Error{Format.END}",
            f"{Format.YELLOW + Format.UNDERLINE}@ line {self.line}{Format.END}: \t{Format.GREY}{self.get_code()}{Format.END}",
            f"{Format.BOLD}PC:{Format.END}     \t{Format.GREY}{self.pc}{Format.END}",
            f"{Format.BOLD}Target:{Format.END} \t{self.var_to}",
        ]
        if self.info:
            message[0] += f": {self.info}"
        return '\n\t'.join(message)


class ExplicitFlowError(FlowError):
    """
    ExplicitFlowError is a flow error that occurs when a variable is assigned
    to and the target variable's labels are not a subset of from variable's labels.
    """

    def __init__(
        self,
        node: ast.AST,
        var_from: FlowVar = None,
        var_to: FlowVar = None,
        info: str = "",
    ) -> None:
        super().__init__(node, var_to, info)
        self.var_from = var_from

    def __str__(self) -> str:
        message = [
            f"{Format.BOLD+Format.ORANGE}Explicit Flow Error{Format.END}",
            f"{Format.YELLOW + Format.UNDERLINE}@ line {self.line}{Format.END}: \t{Format.GREY}{self.get_code()}{Format.END}",
            f"{Format.BOLD}Value:{Format.END}   \t{self.var_from}",
            f"{Format.BOLD}Target:{Format.END} \t{self.var_to}",
        ]
        if self.info:
            message[0] += f": {self.info}"
        return '\n\t'.join(message)
