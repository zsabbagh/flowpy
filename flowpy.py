import ast
import tokenize

FLOWPY_PREFIX = "fp"
functions_to_check = []


class Evaluator:
    def add_labels(self, comment_string: str) -> None:
        pass


# Read comments
with open("ast_demo_input.py", "rb") as f:
    tokens = tokenize.tokenize(f.readline)
    check_next_function = False
    get_function_name = False
    for token in tokens:
        # TODO: Change this? Just in case we ever need to consider whitespace
        if token.type in [tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT]:
            continue

        if token.type == tokenize.COMMENT:
            if token.string.startswith(f"#{FLOWPY_PREFIX}"):
                evaluator = Evaluator()
                check_next_function = True
                evaluator.add_labels(token.string)
        # Run only if we're supposed to evaluate the next function and are out of comments.
        elif check_next_function == True:
            # `def` is a `NAME` token and `async` has its own. Both are acceptable before a function name.
            if token.type != tokenize.NAME and token.type != tokenize.ASYNC:
                raise ValueError(
                    f"Expected function definition, got token type {tokenize.tok_name[token.type]} ({token.string})"
                )

            # Assumes function name always follows the `def` keyword (`def func`, `async def func()`)
            if token.string == "def":
                get_function_name = True
            elif get_function_name:
                functions_to_check.append(token.string)
                get_function_name = False
                check_next_function = False


with open("ast_demo_input.py") as src:
    code = src.read()
    prog = ast.parse(code)

    for nd in ast.walk(prog):
        if isinstance(nd, ast.FunctionDef) and nd.name in functions_to_check:
            print(f"Evaluating function {nd.name} as specified by comments")
