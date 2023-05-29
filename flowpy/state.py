"""
    This file contains the State class, which is used to keep track of the
    current state of variables.
"""
import re
from copy import deepcopy

class State:
    """
    This class handles states.
    A state belongs to a named scope (namespace)
    """

    class __Rule:
        """
        The Rule class is used to store rules.
        Each rule has a regex and a set of labels.
        """

        def __str__(self) -> str:
            return f"Rule {self.regex} -> {self.labels}"

        def __init__(self, restr, labels):
            self.regex = "^" + restr.replace("*", ".*") + "$"
            self.labels = set(labels)

        def add(self, labels):
            self.labels.update(labels)

        def applies_to(self, value):
            return bool(re.search(self.regex, value))

    def combine(self, other) -> None:
        """
        Combines a state with another state,
        i.e. updates the PC and adds all missing labels
        """
        self.__pc.update(other.__pc)
        for regex, rule in other.__rules.items():
            if regex not in self.__rules:
                self.__rules[regex] = rule
            else:
                self.__rules[regex].add(rule.labels)

    def __init__(self):
        """
        Initialise a state.
        """
        self.__rules = {}
        self.__pc = set()
        self.__used = set()
        self.__warnings = []
    
    def get_used(self, what=0) -> None:
        """
        Get all used labels, returns:
        0: labels
        1: vars (dict of vars and their labels)
        2: labels, vars
        """
        labels = set()
        vars = dict()
        for var in self.__used:
            l = self.get_labels(var)
            labels.update(l)
            vars[var] = l
        match what:
            case 0:
                return labels
            case 1:
                return vars
            case 2:
                return labels, vars
            case _:
                return None

    def set_used(self, var) -> None:
        """
        Set a variable as used
        """
        if type(var) == str:
            self.__used.add(var)
        else:
            for v in var:
                self.__used.add(v)

    def copy(self, used=True):
        """
        Returns a copy of this state
        Uses deepcopy to avoid modifying the original state
        In case of a copy, the used labels are not copied
        """
        state = State()
        state.__pc = deepcopy(self.__pc)
        state.__rules = deepcopy(self.__rules)
        state.__used = deepcopy(self.__used)
        state.__warnings = self.__warnings
        return state
    
    def update_used(self, other) -> None:
        """
        Combines the used labels of two states
        """
        self.__used.update(other.__used)

    def error(self, err) -> None:
        """
        Adds an error to the state
        """
        self.__warnings.append(err)
    
    def get_warnings(self) -> list:
        """
        Returns the errors
        """
        return self.__warnings

    def __str__(self) -> str:
        res = ["State: ", f"\t<PC>: {self.__pc}"]
        for regex, rule in self.__rules.items():
            res.append(f"\t{regex}: {rule.labels}")
        res.append(f"\tUsed: {self.__used}")
        return "\n".join(res)

    def update_pc(self, labels) -> None:
        """
        Update PC and adds all missing labels.
        Observe that labels are added, not overwritten.
        """
        if type(labels) == State:
            labels = labels.get_pc()
        elif type(labels) == list:
            labels = set(labels)
        self.__pc.update(labels)

    def set_pc(self, labels: set) -> None:
        """
        Sets PC to labels, i.e. overwrite with labels.
        """
        self.__pc = labels

    def get_pc(self) -> set:
        """
        Gets the PC
        """
        return self.__pc

    def add_rules(self, comment: str) -> None:
        """
        Input string as FlowPy-comment stripped

        Grammar matching:
        label   := [^\s,]+
        labels  := {} | label, labels
        rule    := (PYTHON_VAR_CHARS|*)+: label [, labels]
        rules   := {} | rule. rules

        Example: a: my_label, my_label_2. b: other_label

        """
        rules = list(filter(bool, comment.strip().split(".")))
        for rule in rules:
            try:
                first, second = tuple(re.split(r":", rule))
                regex = re.findall(r"[a-zA-Z0-9_\*]+", first)[0]
                labels = list(
                    filter(bool, (map(lambda x: x.strip(), second.split(","))))
                )
                if regex and labels:
                    labels = list(filter(lambda x: x != "()", labels))
                    if len(labels) == 0:
                        self.__rules[regex] = self.__Rule(regex, set())
                    elif regex not in self.__rules:
                        self.__rules[regex] = self.__Rule(regex, labels)
                    else:
                        self.__rules[regex].add(labels)

            except (ValueError, IndexError) as e:
                print(e)
                continue

    def get_labels(self, variable: str) -> set:
        """
        Input variable name to check.
        Returns labels as a set.
        Gets all rules that apply to the variable and returns
        all of the rules' labels.

        variable: The variable to check
        """
        result = set()
        for _, rule in self.__rules.items():
            if rule.applies_to(variable):
                if len(rule.labels) == 0:
                    return set()
                result.update(rule.labels)
        return result
