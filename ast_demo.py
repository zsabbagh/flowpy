import ast

with open("ast_demo_input.py") as src:
    code = src.read()
    prog = ast.parse(code)
    for nd in ast.walk(prog):
        if isinstance(nd, ast.Assign):
            if not isinstance(nd.value, ast.Tuple):
                print(
                    f"\033[;1mAssigning {nd.value.value} to variable {','.join([t.id for t in nd.targets])}\033[0m"
                )
            else:
                print(
                    f"\033[;1mAssigning {','.join([str(const.value) for const in nd.value.elts])} to variable {','.join([e.id for t in nd.targets for e in t.elts])}\033[0m"
                )

        print(nd)

    print("-- DUMP --")

    print(ast.dump(prog))
