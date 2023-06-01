#!/usr/bin/python3
import ast
import os
import subprocess
import tokenize
from io import BytesIO, IOBase
from pathlib import Path
from sys import stderr, stdin, stdout
from typing import Dict

from .arguments import FLOWPY_PREFIX, MAIN_SCRIPT, Format, args
from .evaluators import Evaluator
from .state import State

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

        def get_lines(self, line, diff=1) -> str:
            """
            Returns the line of code from the source code
            """
            lines = self.source.splitlines()
            botdelta = line - diff
            topdelta = line + diff - len(lines)
            add_to_bot = 0 if botdelta >= 0 else -botdelta
            add_to_top = 0 if topdelta <= 0 else topdelta
            bottom = line - diff - add_to_bot if line-diff-add_to_bot > 0 else 0
            top = line + diff - add_to_top if line+diff-add_to_top < len(lines) else len(lines)-1
            return self.source.splitlines()[bottom:top+1], bottom, top

        def __str__(self) -> str:
            return self.source

        def __init__(self, source: str, encoding: str = "utf-8", name="", is_file=False) -> None:
            self.name = name
            self.source = source
            self.encoding = encoding
            self.functions: Dict[str, State] = {}
            self.global_state = State()
            self.is_file = is_file

        def parse(self) -> None:
            """
            Parses the source code and extracts the comments
            rules for each function.
            """
            tokens = tokenize.tokenize(
                BytesIO(self.source.encode(self.encoding)).readline
            )
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
        return "".join(map(str, self.sources))

    def get_states(self) -> str:
        res = []
        for source in self.sources:
            res.append(f"\nSource {source.name}:")
            for func, state in source.functions.items():
                res.append(f"Function {func}:\n{state}")
        return "\n".join(res)

    def __init__(self, sources=None, sink=stdout, encoding="utf-8") -> None:
        """
        source: Where to read the source code from
        sink: Where to output the results
        """
        self.encoding = encoding
        sources = [sources] if type(sources) != list else sources
        self.sources = []
        name = ""
        is_file = False
        for source in sources:
            if source == stdin:
                name = "stdin"
            source_str = ""
            if isinstance(source, IOBase):
                source_str = source.read()
            elif isinstance(source, str):
                path = Path(source)
                if path.exists():
                    is_file = True
                    name = path.name
                    source_str = open(path, encoding=self.encoding).read()
                else:
                    source_str = source
            else:
                print("Error: Source must be a file or a string", file=stderr)
                exit(1)
            if not name:
                name = 'unnamed-' + os.urandom(8).hex()
            self.sources.append(
                self.Source(source_str, encoding=self.encoding, name=name, is_file=is_file)
            )

            if args.verbose:
                bat_available = False
                try:
                    subprocess.call(["bat", "-V"], stdout=subprocess.DEVNULL)
                    bat_available = is_file
                except:
                    pass

                print(
                    f"\n{Format.GREEN}----- {Format.BOLD}"
                    + f"Source: '{name}'"
                    + f"{Format.END} {Format.GREEN} -----{Format.END}"
                    + "\n"
                )

                # Pretty print if we can
                if bat_available:
                    subprocess.call(["bat", "--number", str(source)])
                    print()

                else:
                    print(
                        f"{self.get_source()}"
                        + "\n"
                    )
                print(f"{Format.GREEN}----- end of source{Format.END} {Format.GREEN} -----{Format.END}")
                print()
        # Why have this when we have functions for each source in self.sources
        # self.functions = {}
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
            state = main_evaluator.evaluate()
            warnings = state.get_warnings()
            print(f"{Format.CYAN}...analysing '{source.name}'...{Format.END}")
            if len(warnings) > 0:
                print(
                    f"\n{Format.RED + Format.UNDERLINE + Format.BOLD}FlowError(s) detected!{Format.END}"
                )
                print(
                    f"{len(warnings)} warnings from source '{Format.UNDERLINE+Format.RED}{source.name}{Format.END}':"
                )
                for warning in warnings:
                    print()
                    print(warning)
                    # print lines of code
                    if args.verbose:
                        print()
                        print(
                            f"{Format.GREY + Format.BOLD}Code context:{Format.END}"
                        )
                        diff = args.diff
                        colour = Format.GREY
                        lines, bottom, top = source.get_lines(warning.line, diff=diff)
                        max = len(str(top))
                        if top-bottom == 0:
                            continue
                        for i, line in enumerate(lines):
                            if bottom+i+1 == warning.line:
                                colour = Format.RED+Format.BOLD
                            else:
                                colour = Format.GREY
                            print(f"{Format.GREY}{bottom+i+1}{' '*(max-len(str(bottom+i+1)))}  {colour}{line}{Format.END}")
                        print()
                    result.append(warning)
            else:
                print(
                    f"{Format.GREEN + Format.BOLD}No FlowErrors detected!{Format.END}"
                )
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
    # print(flowpy.get_states())


if __name__ == "__main__":
    main()
