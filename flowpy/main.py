#!/usr/bin/python3
import ast
import tokenize
import os
from sys import stderr, stdin, stdout
from io import IOBase, BytesIO
from pathlib import Path
from typing import Dict
from .state import State
from .evaluators import Evaluator
from .arguments import args, Format, MAIN_SCRIPT, FLOWPY_PREFIX

# TODO: Print to sink instead of stdout

class FlowPy:
    """
    Wrapper class for the entire program.
    Combines evaluator and state to form the program.

    __init__: Initializes the program with sources as files or strings
    """
    class Source:
        """
        Wrapper class for the source code.
        Responsible for parsing the source code
        and extracting the comments
        """

        name: str
        source: str
        encoding: str
        global_state: State
        functions: Dict[str, State]

        def __str__(self) -> str:
            return self.source

        def __init__(self, source: str, encoding: str = "utf-8", name='') -> None:
            self.name = name
            self.source = source
            self.encoding = encoding
            self.functions: Dict[str, State] = {}
            self.global_state = State()

        def parse(self) -> None:
            """
            Parses the source code and extracts the comments
            rules for each function.
            """
            tokens = tokenize.tokenize(BytesIO(self.source.encode(self.encoding)).readline)
            # We don't really care about these
            to_skip = [tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT]

            expecting_def = False
            upcoming_function_name = False

            state = State()
            for token in tokens:
                if token.type in to_skip:
                    continue
                if token.type == tokenize.COMMENT:
                    comment = token.string[1:].lstrip()
                    if comment.startswith(FLOWPY_PREFIX):
                        expecting_def = True
                        state.add_rules(
                            comment.removeprefix(FLOWPY_PREFIX)
                        )  # Strip the prefix
                # Run only if we're supposed to evaluate the next function and are out of comments.
                elif expecting_def:
                    if token.string == "def":
                        upcoming_function_name = True
                    elif upcoming_function_name:
                        # Bind the state to that function and create a new state for the next
                        self.functions[token.string] = state
                        state = State()
                        upcoming_function_name = False
                        expecting_def = False
                    else:
                        expecting_def = False
                        self.global_state.combine(state)
                        state = State()

            self.functions[MAIN_SCRIPT] = self.global_state


    def get_source(self) -> Source:
        """
        Returns the source code as a Source object
        """
        return ''.join(map(str, self.sources))

    def get_states(self) -> str:
        res = []
        for source in self.sources:
            res.append(f"\nSource {source.name}:")
            for func, state in source.functions.items():
                res.append(f"Function {func}:\n{state}")
        return '\n'.join(res)

    def __init__(self, sources=None, sink=stdout, encoding="utf-8") -> None:
        """
        source: Where to read the source code from
        sink: Where to output the results
        """
        self.encoding = encoding
        sources = [sources] if type(sources) != list else sources
        self.sources = []
        name = ""
        for source in sources:
            if source == stdin:
                name = "stdin"
            source_str = ''
            if isinstance(source, IOBase):
                source_str = source.read()
            elif isinstance(source, str):
                path = Path(source)
                if path.exists():
                    name = path.name
                    source_str = open(path, encoding=self.encoding).read()
                else:
                    source_str = source
            else:
                print("Error: Source must be a file or a string", file=stderr)
                exit(1)
            if not name:
                name = os.urandom(8).hex()
            self.sources.append(self.Source(source_str, encoding=self.encoding, name=name))
        if args.verbose:
            print(f"\n----- Source code: -----\n{self.get_source()}\n-----")
        # Why have this when we have functions for each source in self.sources
        #self.functions = {}
        if not hasattr(sink, "write"):
            print("Error: Sink must have a write method", file=stderr)
            exit(1)
        for source in self.sources:
            source.parse()

    def run(self):
        """
        Runs the program and evaluates the functions.
        Evaluates the code based on the FlowPy comments.
        """
        result = []
        for source in self.sources:
            prog = ast.parse(str(source))
            main_evaluator = Evaluator.from_AST(prog, State(), source.functions)
            warnings = main_evaluator.evaluate()
            if len(warnings) > 0:
                print(f"\n{Format.UNDERLINE+Format.RED}FlowError(s) detected!{Format.END}")
                print(f"{len(warnings)} warnings from source '{Format.UNDERLINE+Format.RED}{source.name}{Format.END}':")
                for warning in warnings:
                    print()
                    print(warning)
                    result.append(warning)
        return result


def main():
    print("~~~ FlowPy v0.1 ~~~")
    if args.verbose:
        print("\n <><< Verbose mode enabled >><> \n")
    if args.file == "stdin":
        args.file = stdin
    if args.verbose:
        print(f"Reading from {args.file}")
    if args.output == "stdout":
        args.output = stdout
    flowpy = FlowPy(args.file, sink=args.output, encoding=args.encoding)
    flowpy.run()
    #print(flowpy.get_states())


if __name__ == "__main__":
    main()
