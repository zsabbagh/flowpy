from abc import ABC, abstractmethod
import ast
import sys
from state import State


class Evaluator(ABC):
    """
    Abstract class for all evaluators to inherit from.
    """

    node: ast.AST
    state: State

    # Superclass for all evaluators
    def __init__(self, node, state):
        self.node = node
        self.state = state

    @staticmethod
    def from_AST(node: ast.AST, state):
        """
        Depending on type of node, return the appropriate subclass
        """
        match node.__class__:
            case ast.If:
                return IfEvaluator(node, state)
            case ast.Assign:
                return AssignEvaluator(node, state)
            case ast.Expr:
                return ExprEvaluator(node, state)
            case ast.Call:
                return CallEvaluator(node, state)
            case _:
                return UnimplementedEvaluator(node, state)

    @staticmethod
    # Print a warning message
    def warn(msg: str):
        """
        Print a warning message
        """
        print("\033[33;1mWARNING:\033[0m", f"\033[;1m{msg}\033[0m", file=sys.stderr)

    @abstractmethod
    def evaluate(self) -> bool:
        """
        Evaluate the contents of a node.
        PC must be saved and reset at beginning and end respectively.
        """
        expression_OK = True
        return expression_OK


class UnimplementedEvaluator(Evaluator):
    """
    The default evaluator to return if one is not implemented
    for the node in question.
    This will also have an `evaluate` method, meaning that we won't get
    AttributeErrors from trying to check an unimplemented node.
    """

    node: ast.AST
    state: State

    def __init__(self, node: ast.AST, state: State):
        super().__init__(node, state)

    def evaluate(self) -> bool:
        print(f"Evaluator not implemented for node {type(self.node)}.", file=sys.stderr)
        return True


class FunctionEvaluator(Evaluator):
    """
    Evaluate a function.
    """

    node: ast.FunctionDef
    state: State

    def __init__(self, node: ast.FunctionDef, state: State):
        super().__init__(node, state)

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
        super().__init__(node, state)

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
        # `elif`s are represented as an `if` inside the `orelse` list.
        for nd in self.node.body + self.node.orelse:
            evaluator = Evaluator.from_AST(nd, self.state)
            evaluator.evaluate()

        self.state.set_pc(pc)
        return True


class AssignEvaluator(Evaluator):
    node: ast.Assign
    state: State

    def __init__(self, node: ast.Assign, state: State):
        super().__init__(node, state)

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
                        Evaluator.warn(
                            f"Assigning {self.node.value.id} to {tgt.id}, where {tgt.id} has labels {target_labels} and {self.node.value.id} has labels {value_labels}."
                        )
                        return False
                    # If target is missing any of the labels in PC, warn.
                    if not self.state.get_pc().issubset(target_labels):
                        Evaluator.warn(
                            f"Assigning to variable {tgt.id} with labels {target_labels} despite PC being {self.state.get_pc}"
                        )
                else:
                    print(
                        f"Assigning to node {type(self.node.value)} not yet supported"
                    )

        # TODO: This is very similar to the ast.Name case. Perhaps do something to avoid code duplication?
        # Only real difference here is that we don't care about the value's labels (as it's a constant and doesn't have any).
        elif isinstance(self.node.value, ast.Constant):
            for tgt in self.node.targets:
                if isinstance(tgt, ast.Name):
                    target_labels = self.state.get_labels(tgt.id)
                    if not self.state.get_pc().issubset(target_labels):
                        Evaluator.warn(
                            f"Assigning to variable {tgt.id} with labels {target_labels} despite PC being {self.state.get_pc}"
                        )

        else:
            print(f"Assigning node {type(self.node.value)} not yet supported")

        # No "invalid" assignments have occurred
        return True


class ExprEvaluator(Evaluator):
    """
    'When an expression, such as a function call, appears as a statement by
    itself with its return value not used or stored, it is wrapped in this
    container [Expr].' - https://docs.python.org/3/library/ast.html

    In other words, an Expr holds an expression whose value is unused. The most
    likely thing in a naïve program will probably be `Call`s to functions with
    side effects, such as `print()`.
    """

    node: ast.Expr
    state: State

    def __init__(self, node: ast.Expr, state: State):
        super().__init__(node, state)

    # Since an expression acts as a wrapper, we just defer
    # IFC to the wrapped node.
    def evaluate(self) -> bool:
        evaluator = Evaluator.from_AST(self.node.value, self.state)
        return evaluator.evaluate()


class CallEvaluator(Evaluator):
    """
    Evaluate a function call.

    In the future, we could perhaps follow these flows and check the called
    function as well, but for now, just warn about potential issues.

    Also, this currently only considers calling named functions (i.e. nodes
    of type ast.Name). Any others will print an error message.
    """

    node: ast.Call
    state: State

    def __init__(self, node: ast.Call, state: State):
        super().__init__(node, state)

    def evaluate(self) -> bool:
        if self.state.get_pc():  # PC empty -> no restrictions
            if isinstance(self.node.func, ast.Name):
                Evaluator.warn(
                    f"Calling function {self.node.func.id} with non-empty PC ({self.state.get_pc()}). Currently, FlowPy won't follow these calls, meaning that any side effects may result in information leakage."
                )
            else:
                print(f"Call not implemented for type {self.node.func}")

            return False

        for arg in self.node.args:
            if isinstance(arg, ast.Constant):
                continue
            elif isinstance(arg, ast.Name):
                if isinstance(self.node.func, ast.Name):
                    Evaluator.warn(
                        f"Calling function {self.node.func.id} with {arg.id} as an argument, which has labels {self.state.get_labels(arg.id)}. Currently, FlowPy won't follow these calls, meaning that any side effects may result in information leakage."
                    )
            else:
                print(f"Call not implemented for type {self.node.func}")

            return False

        return True
