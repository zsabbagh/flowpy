import ast
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Tuple
from .state import State
from .arguments import args, MAIN_SCRIPT
from .errors import FlowError, ImplicitFlowError, ExplicitFlowError, FlowVar


# TODO: RETURN labels AND warnings
class Evaluator(ABC):
    """
    Abstract class for all evaluators to inherit from.
    """

    node: ast.AST
    state: State
    function_states: Dict[str, State]

    # Superclass for all evaluators
    def __init__(self, node, state, function_states):
        self.node = node
        self.state = state
        self.function_states = function_states

    @staticmethod
    def from_AST(node: ast.AST, state: State, function_states: Dict[str, State]):
        """
        Depending on type of node, return the appropriate subclass
        """
        match node.__class__:
            case ast.If:
                return IfEvaluator(node, state, function_states)
            case ast.Assign:
                return AssignEvaluator(node, state, function_states)
            case ast.Expr:
                return ExprEvaluator(node, state, function_states)
            case ast.Call:
                return CallEvaluator(node, state, function_states)
            case ast.FunctionDef:
                return FunctionDefEvaluator(node, state, function_states)
            case ast.Module:
                return ModuleEvaluator(node, state, function_states)
            case ast.While:
                return WhileEvaluator(node, state, function_states)
            case ast.Pass:
                return PassEvaluator(node, state, function_states)
            case ast.IfExp:
                return IfExpEvaluator(node, state, function_states)
            case ast.Compare:
                return CompareEvaluator(node, state, function_states)
            case ast.Name:
                return NameEvaluator(node, state, function_states)
            case ast.Tuple:
                return TupleEvaluator(node, state, function_states)
            case ast.Constant:
                return ConstantEvaluator(node, state, function_states)
            case ast.For:
                return ForEvaluator(node, state, function_states)
            case _:
                return UnimplementedEvaluator(node, state, function_states)

    @staticmethod
    # Print a warning message
    def warn(msg: str, line: int):
        """
        Print a warning message
        """
        if args.verbose:
            print(
                "\033[33;1m" + f"WARNING (line {line}):" + "\033[0m",
                f"\033[;1m{msg}\033[0m",
                file=sys.stderr,
            )

    @abstractmethod
    def evaluate(self) -> bool:
        """
        Evaluate the contents of a node.
        PC must be saved and reset at beginning and end respectively.
        Always returns (warnings, labels of variables in PC)
        """
        expression_OK = []
        return expression_OK, dict()


class UnimplementedEvaluator(Evaluator):
    """
    The default evaluator to return if one is not implemented
    for the node in question.
    This will also have an `evaluate` method, meaning that we won't get
    AttributeErrors from trying to check an unimplemented node.
    """

    node: ast.AST
    state: State
    function_states: Dict[str, State]

    def __init__(self, node: ast.AST, state: State, function_states: Dict[str, State]):
        super().__init__(node, state, function_states)

    def evaluate(self) -> List[FlowError]:
        # TODO: Make verbosable
        Evaluator.warn(
            f"Evaluator NOT IMPLEMENTED for node {type(self.node)}.", self.node.lineno
        )
        return self.state


class NameEvaluator(Evaluator):
    """
    Evaluate a name.
    Crucial for error reporting.
    """

    def __init__(self, node, state, function_states):
        super().__init__(node, state, function_states)

    def evaluate(self) -> State:
        """
        Evaluate a name.
        """
        curr_labels = self.state.get_labels(self.node.id)
        if type(self.node.ctx) == ast.Store:
            # Report errors if the variable is missing any labels in PC
            used_labels = self.state.get_used(0)
            if not used_labels.issubset(curr_labels):
                self.state.error(
                    ExplicitFlowError(
                        self.node,
                        self.state,
                        FlowVar(self.node.id, curr_labels),
                        f"Target missing used labels {used_labels - curr_labels}",
                    )
                )
            if not self.state.get_pc().issubset(curr_labels):
                self.state.error(
                    ImplicitFlowError(
                        self.node,
                        self.state,
                        FlowVar(self.node.id, curr_labels),
                        f"Target missing PC labels {self.state.get_pc() - curr_labels}",
                    )
                )
        elif type(self.node.ctx) == ast.Load:
            self.state.set_used(self.node.id)
        return self.state


class TupleEvaluator(Evaluator):
    """
    Evaluate a tuple.
    """

    def __init__(self, node, state, function_states):
        super().__init__(node, state, function_states)

    def evaluate(self) -> bool:
        for nd in self.node.elts:
            evaluator = Evaluator.from_AST(nd, self.state.copy(), self.function_states)
            state = evaluator.evaluate()
            self.state.update_used(state)
        return self.state


class ConstantEvaluator(Evaluator):
    """
    Evaluate a constant.
    """

    def __init__(self, node, state, function_states):
        super().__init__(node, state, function_states)

    def evaluate(self) -> bool:
        return self.state


class FunctionDefEvaluator(Evaluator):
    """
    Evaluate a function.
    """

    node: ast.FunctionDef
    state: State
    function_states: Dict[str, State]

    def __init__(
        self, node: ast.FunctionDef, state: State, function_states: Dict[str, State]
    ):
        super().__init__(node, state, function_states)

        if self.node.name in self.function_states:
            self.state.combine(self.function_states[self.node.name])

    def evaluate(self) -> List[FlowError]:
        # for all nodes in the function
        for nd in self.node.body:
            evaluator = Evaluator.from_AST(nd, self.state.copy(), self.function_states)
            evaluator.evaluate()
        return self.state


class IfExpEvaluator(Evaluator):
    """
    If expression evaluator.
    """

    def __init__(self, node, state, function_states):
        super().__init__(node, state, function_states)

    def evaluate(self) -> List[FlowError]:
        state = Evaluator.from_AST(
            self.node.test, self.state.copy(), self.function_states
        ).evaluate()
        used = state.get_used()
        self.state.set_used(used)
        self.state.update_pc(used)
        Evaluator.from_AST(
            self.node.body, self.state.copy(), self.function_states
        ).evaluate()
        Evaluator.from_AST(
            self.node.orelse, self.state.copy(), self.function_states
        ).evaluate()
        return self.state


class CompareEvaluator(Evaluator):
    """
    Evaluate a comparison.
    """

    def __init__(self, node, state, function_states):
        super().__init__(node, state, function_states)

    def evaluate(self) -> Tuple[List[FlowError], Set[str]]:
        # Check the LHS plus all the other variables/elements in the statement
        items = list(
            self.node.comparators
        )  # Not the LHS (list as we may have a == b == c or smth)
        items.append(self.node.left)  # The LHS
        for item in items:
            state = Evaluator.from_AST(
                item, self.state.copy(), self.function_states
            ).evaluate()
            self.state.update_used(state)
        return self.state


class IfEvaluator(Evaluator):
    node: ast.If
    state: State
    function_states: Dict[str, State]

    def __init__(self, node: ast.If, state: State, function_states: Dict[str, State]):
        super().__init__(node, state, function_states)

    # If statements have a "test" (the conditional) which holds one node.
    # By looking at the Python grammar, the type this node may have is not that
    # restricted, but we should probably just assume we have a `name` or `compare`
    # for now (i.e. "if a" and "if a == b") as that gives a more reasonable scope.
    def evaluate(self) -> List[FlowError]:
        """
        Evaluate the contents of an if statement.
        """
        state = Evaluator.from_AST(
            self.node.test, self.state.copy(), self.function_states
        ).evaluate()
        self.state.update_pc(state.get_used())
        # `elif`s are represented as an `if` inside the `orelse` list.
        for nd in self.node.body + self.node.orelse:
            Evaluator.from_AST(nd, self.state.copy(), self.function_states).evaluate()

        return self.state


class AssignEvaluator(Evaluator):
    node: ast.Assign
    state: State
    function_states: Dict[str, State]

    def __init__(
        self, node: ast.Assign, state: State, function_states: Dict[str, State]
    ):
        super().__init__(node, state, function_states)

    def evaluate(self) -> bool:
        # Only support assignment of simple variables so far
        # (no lists, dicts etc. on RHS)
        states = []
        if hasattr(self.node.value, "elts"):
            # iterable values
            for elt in self.node.value.elts:
                states.append(
                    Evaluator.from_AST(
                        elt, self.state.copy(), self.function_states
                    ).evaluate()
                )
        else:
            states.append(
                Evaluator.from_AST(
                    self.node.value, self.state.copy(), self.function_states
                ).evaluate()
            )
        for tgt in self.node.targets:
            if hasattr(tgt, "elts"):
                for i in range(len(states)):
                    Evaluator.from_AST(
                        tgt.elts[i], states[i].copy(), self.function_states
                    ).evaluate()
            else:
                state = self.state.copy()
                for s in states:
                    state.update_used(s)
                Evaluator.from_AST(tgt, state, self.function_states).evaluate()
        # No "invalid" assignments have occurred
        return self.state


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
    function_states: Dict[str, State]

    def __init__(self, node: ast.Expr, state: State, function_states: Dict[str, State]):
        super().__init__(node, state, function_states)

    # Since an expression acts as a wrapper, we just defer
    # IFC to the wrapped node.
    def evaluate(self) -> List[FlowError]:
        evaluator = Evaluator.from_AST(
            self.node.value, self.state.copy(), self.function_states
        )
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
    function_states: Dict[str, State]

    def __init__(self, node: ast.Call, state: State, function_states: Dict[str, State]):
        super().__init__(node, state, function_states)

    def evaluate(self) -> List[FlowError]:
        state = Evaluator.from_AST(
            self.node.func, self.state.copy(), self.function_states
        ).evaluate()
        self.state.update_pc(state)
        if self.state.get_pc():
            self.state.error(
                ImplicitFlowError(
                    self.node,
                    self.state,
                    FlowVar(
                        self.node.func.id, self.state.get_labels(self.node.func.id)
                    ),
                    f"Untracked function call {self.node.func.id} with PC labels {self.state.get_pc()}",
                )
            )
        for arg in self.node.args:
            state = Evaluator.from_AST(arg, self.state.copy(), self.function_states).evaluate()
            self.state.update_used(state)
        return self.state


class ForEvaluator(Evaluator):
    """
    Evaluate a for loop.
    """
    def __init__(self, node, state, function_states):
        super().__init__(node, state, function_states)
    
    def evaluate(self) -> bool:
        state = Evaluator.from_AST(
            self.node.iter, self.state.copy(), self.function_states
        ).evaluate()
        self.state.update_pc(state.get_used())
        for nd in self.node.body:
            Evaluator.from_AST(nd, self.state.copy(), self.function_states).evaluate()
        return self.state

class WhileEvaluator(Evaluator):
    """
    Evaluate a while loop.
    """

    def __init__(self, node, state, function_states):
        super().__init__(node, state, function_states)

    def evaluate(self) -> bool:
        state = Evaluator.from_AST(
            self.node.test, self.state.copy(), self.function_states
        ).evaluate()
        self.state.update_pc(state.get_used())
        for nd in self.node.body:
            evaluator = Evaluator.from_AST(nd, self.state.copy(), self.function_states)
            state = evaluator.evaluate()
        return self.state


class PassEvaluator(Evaluator):
    """
    Evaluate a pass statement.
    """

    def __init__(self, node, state, function_states):
        super().__init__(node, state, function_states)

    def evaluate(self) -> List[FlowError]:
        return self.state


class ModuleEvaluator(Evaluator):
    """
    Evaluate a module. This is basically the root of the entire AST for
    "regular" python files.
    """

    node: ast.Module
    state: State
    function_states: Dict[str, State]

    def __init__(
        self, node: ast.Module, state: State, function_states: Dict[str, State]
    ):
        super().__init__(node, state, function_states)
        if MAIN_SCRIPT in self.function_states:
            self.state.combine(self.function_states[MAIN_SCRIPT])

    def evaluate(self) -> bool:
        for nd in self.node.body:
            evaluator = Evaluator.from_AST(nd, self.state.copy(), self.function_states)
            evaluator.evaluate()
        return self.state
