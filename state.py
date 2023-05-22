"""
    This file contains the State class, which is used to keep track of the
    current state of variables.
"""
import re


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

        def __init__(self, restr, labels):
            self.regex = "^" + restr.replace("*", ".*") + "$"
            self.labels = set(labels)

        def add(self, labels):
            self.labels.update(labels)

        def applies_to(self, value):
            return bool(re.search(self.regex, value))

    def __init__(self, parent_state=None):
        """
        If parent_state is provided,
        PC is inherited and get_labels becomes
        (potentially) recursive, if no matches exists
        in the current state.
        """
        self.__rules = {}
        self.__pc = set()
        self.__parent = parent_state
        if parent_state is not None:
            self.__pc = parent_state.__pc

    def __str__(self):
        res = ["State: \n", f"\t<PC>: {self.__pc}\n\t"]
        for regex, rule in self.__rules.items():
            res.append(f"{regex}: {rule.labels}\n\t")
        return "".join(res)

    def update_pc(self, labels):
        """
        Update PC and adds all missing labels
        """
        self.__pc.update(labels)

    def set_pc(self, labels: set):
        """
        Sets PC to labels, i.e. overwrite with labels
        """
        self.__pc = labels

    def get_pc(self):
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
                labels = list(map(lambda x: x.strip(), second.split(",")))
                if regex and labels:
                    if regex not in self.__rules:
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
        Checks parent state if it exists.
        """
        result = set()
        for _, rule in self.__rules.items():
            if rule.applies_to(variable):
                result.update(rule.labels)
        # Recursively check labels if none is find
        if len(result) == 0 and type(self.__parent) == State:
            result = self.__parent.get_labels(result)
        return result
