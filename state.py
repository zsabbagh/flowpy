import ast
import tokenize
import re
import sys
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('-f', '--file', help='File to check')
parser.add_argument('-d', '--debug', action='store_true', help='Debug messages')
args = parser.parse_args()

FLOWPY_PREFIX = "fp"
functions_to_check = []

# keep track of state
# TODO: Add variable scope ID

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
            self.regex = '^' + restr.replace('*', '.*') + '$'
            self.labels = set(labels)
        
        def add(self, labels):
            self.labels.update(labels)

        def check(self, value):
            return bool(re.search(self.regex, value))

    def __init__(self):
        self.__rules = {}
        self.__pc = set()
    
    def __str__(self):
        res  = ["State: \n", f"\t<PC>: {self.__pc}\n\t"]
        for (regex, check) in self.__rules.items():
            res.append(f"{regex}: {check.labels}\n\t")
        return ''.join(res)
    
    def __add_rule(self, regex, labels):
        """
            Add labels to the restr (regex string) state
        """
        if regex not in self.__rules:
            self.__rules[regex] = self.__Rule(regex, labels)
        else:
            self.__rules[regex].add(labels)

    def add_rules(self, comment: str) -> None:
        """
            Looks on labels after colon
            Assumes comment = #fp ...
        """
        rules = list(filter(bool, comment[3:].strip().split('.')))
        for rule in rules:
            try:
                first, second = tuple(re.split(r':', rule))
            except ValueError as e:
                continue
            regex = re.findall(r'[a-zA-Z0-9_\*]+', first)
            labels = list(map(lambda x : x.strip(), second.split(',')))
            if regex and labels:
                self.__add_rule(regex[0], labels)
    
    def get_labels(self, variable):
        result = set()
        for (_, rule) in self.__rules.items():
            if rule.check(variable):
                result.update(rule.labels)
        return result

if __name__=='__main__':
    state = State()
    state.add_rules('#fp p*: high. ap*: __-$`.')
    print(state)
    print(state.get_labels('apa'))
    print(state.get_labels('pa'))
