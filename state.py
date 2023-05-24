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
        A checker class to see if a label matches
        TODO: Might be computationally costly.
        Maybe use prefix or substring instead?
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
        Combines a state with another state
        """
        self.__pc.update(other.__pc)
        for regex, rule in other.__rules.items():
            if regex not in self.__rules:
                self.__rules[regex] = rule
            else:
                self.__rules[regex].add(rule.labels)
    
    def __init__(self, other=None):
        """
        If other is a State, copy it.

        other: A state to copy
        """
        self.__rules = {}
        self.__pc = set()
        if type(other)==State:
            self.__pc = deepcopy(other.__pc)
            self.__rules = deepcopy(other.__rules)

    def __str__(self):
        res = ["State: \n", f"\t<PC>: {self.__pc}"]
        for regex, rule in self.__rules.items():
            res.append(f"\t{regex}: {rule.labels}")
        return "\n".join(res)

    def update_pc(self, labels):
        """
        Update PC and adds all missing labels
        """
        self.__pc.update(labels)

    def set_pc(self, labels: set) -> None:
        """
        Sets PC to labels, i.e. overwrite with labels
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
                labels = list(filter(bool, (map(lambda x: x.strip(), second.split(",")))))
                if regex and labels:
                    labels = list(filter(lambda x : x != '()', labels))
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

        variable: The variable to check
        """
        result = set()
        for _, rule in self.__rules.items():
            if rule.applies_to(variable):
                if rule.labels == set():
                    return set()
                result.update(rule.labels)
        return result
