from abc import ABC, abstractmethod
import ast
from state import State

"""
    Abstract class for all evaluators to inherit from.
"""


class Evaluator(ABC):
    @staticmethod
    # depending on type of node, return the appropriate subclass
    def from_AST(node: ast.AST, state):
        if isinstance(node, ast.If):
            return IfEvaluator(node, state)
        elif isinstance(node, ast.Assign):
            return AssignEvaluator(node, state)
        else:
            return UnimplementedEvaluator(node, state)

    """
        Evaluate the contents of a node.
        PC must be saved and reset at beginning and end respectively.
    """

    @abstractmethod
    def evaluate(self) -> bool:
        expression_OK = True
        return expression_OK


class UnimplementedEvaluator(Evaluator):
    node: ast.AST
    state: State

    def __init__(self, node: ast.AST, state: State):
        self.node = node
        self.state = state

    def evaluate(self) -> bool:
        print(f"Evaluator not implemented for node {type(self.node)}.")
        return True


"""
    Evaluate a function.
"""


class FunctionEvaluator(Evaluator):
    node: ast.FunctionDef
    state: State

    def __init__(self, node: ast.FunctionDef, state: State):
        self.node = node
        self.state = state

    def evaluate(self) -> bool:
        pc = self.state.get_pc()

        # for all nodes in the function
        for nd in self.node.body:
            evaluator = Evaluator.from_AST(nd, self.state)
            if not evaluator:
                continue

            if not evaluator.evaluate():
                print(f"\tin function {self.node.name} (line {nd.lineno})")
                return False

        self.state.set_pc(pc)
        return True


class IfEvaluator(Evaluator):
    node: ast.If
    state: State

    def __init__(self, node: ast.If, state: State):
        self.node = node
        self.state = state

    # If statements have a "test" (the conditional) which holds one node.
    # By looking at the Python grammar, the type this node may have is not that
    # restricted, but we should probably just assume we have a `name` or `compare`
    # for now (i.e. "if a" and "if a == b") as that gives a more reasonable scope.
    def evaluate(self) -> bool:
        pc = self.state.get_pc()

        # First, update PC
        if isinstance(self.node.test, ast.Compare):  # If we have e.g. "if a == b"
            # Check the LHS plus all the other variables/elements in the statement
            items = (
                self.node.test.comparators
            )  # Not the LHS (list as we may have a == b == c or smth)
            items.append(self.node.test.left)  # The LHS
            for item in items:
                if isinstance(item, ast.Name):  # If we have a variable
                    # Get all labels of the variable and update state's PC with them
                    # If the set is empty, well, then PC remains unchanged.
                    self.state.update_pc(self.state.get_labels(item.id))
        elif isinstance(self.node.test, ast.Name):  # If we have e.g. "if a"
            self.state.update_pc(self.state.get_labels(self.node.test.id))
        else:
            print(
                f"[Line {self.node.test.lineno}] Test type {type(self.node.test)} not supported. Currently supported types are ast.Compare and ast.Name."
            )

        # TODO: Check that everything in the body is OK according to PC
        # this includes `orelse` tokens.
        for item in self.node.body:
            print(item)
            evaluator = Evaluator.from_AST(item, self.state)
            print(evaluator)
            # Will fail when we have non-supported expressions
            evaluator.evaluate()

        self.state.set_pc(pc)
        return True


class AssignEvaluator(Evaluator):
    node: ast.Assign
    state: State

    def __init__(self, node: ast.Assign, state: State):
        self.node = node
        self.state = state

    def evaluate(self) -> bool:
        # Only support assignment of simple variables so far
        # (no lists, dicts etc. on RHS)
        if isinstance(self.node.value, ast.Name):
            value_labels = self.state.get_labels(self.node.value.id)
            for tgt in self.node.targets:
                if isinstance(tgt, ast.Name):
                    target_labels = self.state.get_labels(tgt.id)

                    # If the assingned value has any labels that the target doesn't, warn.
                    if not value_labels.issubset(target_labels):
                        print(
                            f"WARNING: Assigning {self.node.value.id} to {tgt.id}, where {tgt.id} has labels {target_labels} and {self.node.value.id} has labels {value_labels}."
                        )
                        return False
                    # If target is missing any of the labels in PC, warn.
                    if not self.state.get_pc().issubset(target_labels):
                        print(
                            f"WARNING: Assigning to variable {tgt.id} with labels {target_labels} despite PC being {self.state.get_pc}"
                        )
                else:
                    print(
                        f"Assigning to node {type(self.node.value)} not yet supported"
                    )

        else:
            print(f"Assigning node {type(self.node.value)} not yet supported")

        # No "invalid" assignments have occurred
        return True
