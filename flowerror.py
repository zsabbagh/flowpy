# Purpose: Defines the base class for all flow faults.
class FlowError(Exception):
    """
    Base class for defining all flow faults.
    Could be raised but also treated as a regular object.
    """

    def __init__(self, explicit, linenr=-1, pc: set=None, labels_from: set=None, labels_to: set=None, context: str=None) -> None:
        """
        Initialise a flow fault.

        explicit: True if the fault is explicit, False if implicit
        linenr: The line number of the fault
        pc: The program counter when the fault occurred
        labels_from: The labels that information flows from
        labels_to: The labels that information flows to
        """
        self.message = "Explicit" if explicit else "Implicit"
        self.linenr = linenr
        self.pc = pc
        self.labels_from = labels_from
        self.labels_to = labels_to
        self.context = context
    
    def __str__(self) -> str:
        message = [
            f"{self.message} flow fault @{self.linenr}.",
            f"\tPC:  \t{self.pc}",
            f"\tFlow:\t{self.labels_from} -> {self.labels_to}",
            f"----- Context -----\n{self.context}\n-------------------"
        ]
        return "\n".join(message)
