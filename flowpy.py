import ast
import tokenize
import re
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('file', help='File to check')
parser.add_argument('-d', '--debug', action='store_true', help='Debug messages')
args = parser.parse_args()

FLOWPY_PREFIX = "fp"
functions_to_check = []

# keep track of state

class State:
    """
        This class handles states.
        A state belongs to a named scope (namespace)
    """
    class Check:
        """
            A checker class to see if a label matches
            TODO: Might be computationally costly.
            Maybe use prefix or substring instead?
        """
        def __init__(self, restr, labels):
            self._regex = restr
            self._labels = set(labels)

        def add(self, labels):
            map(lambda label : self._labels.add(label), labels)

        def check(self, value):
            return bool(re.search(self._regex, value))

    def __init__(self):
        self._state = {}
    
    def add_state(self, restr, labels):
        """
            Add labels to the restr (regex string) state
        """
        def check(x):
            return bool(re.search(restr, x))
        if restr not in self._state:
            self._state[restr] = self.Check(restr, labels)
        else:
            self._state[restr].add(labels)

    def add_labels(self, comment_string: str) -> None:
        """
            Looks on labels after colon
        """
        splits = list(filter(bool, re.split(r'#fp |:', comment_string)))
        if len(splits) < 2:
            return
        if args.debug:
            print(f"split 0: {splits[0]}")
            print(f"split 1: {splits[1]}")
        regex = re.search(r'[a-zA-Z0-9\._\*]+', splits[0])
        labels = re.findall(r'[a-zA-Z0-9_]+', splits[1])
        if args.debug:
            print(f"regex: {regex.string}")
        if regex and labels:
            self.add_state(regex.string, labels)
        if args.debug:
            print(self._state)

# Read comments
with open(args.file, "rb") as f:
    tokens = tokenize.tokenize(f.readline)
    to_skip = [tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT]
    check_next_definition = False
    upcoming_function = False
    functions_visited = {}
    state = State()
    for token in tokens:
        if token.type in to_skip:
            continue
        if token.type == tokenize.COMMENT:
            if token.string.startswith(f"#{FLOWPY_PREFIX}"):
                check_next_definition = True
                state.add_labels(token.string)
        # Run only if we're supposed to evaluate the next function and are out of comments.
        elif check_next_definition:
            print(token)
            if token.string == "def":
                upcoming_function = True
            elif upcoming_function:
                if token.string not in functions_to_check:
                    functions_visited[token.string] = False
                upcoming_function = False
                check_next_definition = False


with open(args.file) as src:
    code = src.read()
    prog = ast.parse(code)
    print(ast.dump(prog, indent=2))

    for nd in ast.walk(prog):
        if isinstance(nd, ast.FunctionDef) and nd.name in functions_to_check:
            print(f"Evaluating function {nd.name} as specified by comments")
