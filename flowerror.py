from flowpy import Format

class FlowVar:
    """
    FlowVar is a wrapper class for a variable name and its labels.
    """

    def __init__(self, name, labels):
        self.name = name
        self.labels = labels

    def __str__(self):
        return f"{self.name} : {self.labels}"


# Purpose: Defines the base class for all flow faults.
class FlowError(Exception):
    """
    Base class for defining all flow error.
    Could be raised but also treated as a regular object.
    """

    def __init__(
        self,
        linenr=None,
        var_to=None,
        info="",
    ) -> None:
        """
        Initialise a flow error.
        """
        self.linenr: int = linenr
        self.var_to: FlowVar = var_to
        self.info: str = info

class ImplicitFlowError(FlowError):
    """
    ImplicitFlowError is a flow error that occurs when a variable is assigned
    to when PC is not a subset of the variable's labels.
    """

    def __init__(
        self, linenr=-1, pc: set = None, var_to: FlowVar = None, info: str = ""
    ) -> None:
        super().__init__(linenr, var_to, info)
        self.pc = pc

    def __str__(self) -> str:
        message = [
            f"{Format.BOLD+Format.ORANGE}Implicit Flow Error{Format.END} {Format.YELLOW + Format.UNDERLINE}@ line {self.linenr}{Format.END}",
            f"{Format.GREY}PC:{Format.END}     \t{self.pc}",
            f"{Format.GREY}Variable:{Format.END} \t{self.var_to}",
        ]
        if self.info:
            message.append(f"Info: {self.info}")
        return '\n\t'.join(message)


class ExplicitFlowError(FlowError):
    """
    ExplicitFlowError is a flow error that occurs when a variable is assigned
    to and the target variable's labels are not a subset of from variable's labels.
    """

    def __init__(
        self,
        linenr: int = None,
        var_from: FlowVar = None,
        var_to: FlowVar = None,
        info: str = "",
    ) -> None:
        super().__init__(linenr, var_to, info)
        self.var_from = var_from

    def __str__(self) -> str:
        message = [
            f"{Format.BOLD+Format.ORANGE}Explicit Flow Error{Format.END} {Format.YELLOW + Format.UNDERLINE}@ line {self.linenr}{Format.END}",
            f"{Format.GREY}Variable:{Format.END} \t{self.var_from}",
            f"{Format.GREY}Target:{Format.END} \t{self.var_to}",
        ]
        if self.info:
            message.append(f"Info: {self.info}")
        return '\n\t'.join(message)
