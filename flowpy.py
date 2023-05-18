import ast
import tokenize
import re
from state import State
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('file', help='File to check')
parser.add_argument('-d', '--debug', action='store_true', help='Debug messages')
args = parser.parse_args()

FLOWPY_PREFIX = "fp"
functions_to_check = []

# Read comments
with open(args.file, "rb") as f:
    tokens = tokenize.tokenize(f.readline)
    # We don't really care about these
    to_skip = [tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT]

    expecting_def = False
    upcoming_function_name = False

    # Do we want one state per function or one state for all functions?
    state = State()
    for token in tokens:
        if token.type in to_skip:
            continue
        if token.type == tokenize.COMMENT:
            if token.string.startswith(f"#{FLOWPY_PREFIX}"):
                expecting_def = True
                state.add_rules(token.string)
        # Run only if we're supposed to evaluate the next function and are out of comments.
        elif expecting_def:
            if token.string == "def":
                upcoming_function_name = True
            elif upcoming_function_name:
                functions_to_check.append(token.string)
                upcoming_function_name = False
                expecting_def = False


with open(args.file) as src:
    code = src.read()
    prog = ast.parse(code)
    print(ast.dump(prog, indent=2))

    for nd in ast.walk(prog):
        if isinstance(nd, ast.FunctionDef) and nd.name in functions_to_check:
            print(f"Evaluating function {nd.name} as specified by comments")
