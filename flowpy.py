import ast
import tokenize
import re
from typing import Dict
from state import State
from argparse import ArgumentParser
from evaluators import *

parser = ArgumentParser()
parser.add_argument('file', help='File to check')
parser.add_argument('-d', '--debug', action='store_true', help='Debug messages')
args = parser.parse_args()

FLOWPY_PREFIX = "fp"
# Dict of function_name -> state
functions_to_check: Dict[str, State] = {}

# Parse comments
with open(args.file, "rb") as f:
    tokens = tokenize.tokenize(f.readline)
    # We don't really care about these
    to_skip = [tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT]

    expecting_def = False
    upcoming_function_name = False

    # TODO: Use one state for the entire run, or one per function? One per function, I guess.
    state = State()
    for token in tokens:
        if token.type in to_skip:
            continue
        if token.type == tokenize.COMMENT:
            if token.string.startswith(f"#{FLOWPY_PREFIX}"):
                expecting_def = True
                state.add_rules(token.string.removeprefix(f"#{FLOWPY_PREFIX}")) # Strip the prefix
        # Run only if we're supposed to evaluate the next function and are out of comments.
        elif expecting_def:
            if token.string == "def":
                upcoming_function_name = True
            elif upcoming_function_name:
                # Bind the state to that function and create a new state for the next
                functions_to_check[token.string] = state
                state = State()
                upcoming_function_name = False
                expecting_def = False

with open(args.file) as src:
    code = src.read()
    prog = ast.parse(code)

    for nd in ast.walk(prog):
        if isinstance(nd, ast.FunctionDef) and nd.name in functions_to_check.keys():
            # Evaluate the function
            print(f"Evaluating function {nd.name} as specified by comments")
            evaluator = FunctionEvaluator(nd, functions_to_check[nd.name])
            evaluator.evaluate()
