from argparse import ArgumentParser

parser = ArgumentParser(prog="flowpy", description="Flowpy")
parser.add_argument("file", nargs="*", help="File(s) to check, defaults to stdin", default='stdin')
parser.add_argument("-v", "--verbose", action="store_true", help="Verbose messages")
parser.add_argument("-e", "--encoding", help="Encoding to use", default='utf-8')
parser.add_argument("-o", "--output", help="Output file", default='stdout')
parser.add_argument("-c", "--colour", action="store_true", help="Colour output")
parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
args = parser.parse_args()

MAIN_SCRIPT = '__global_script__'
FLOWPY_PREFIX = "fp"

class Format:
    """
    Class for formatting output
    """
    UNDERLINE = '\033[4m' if args.colour else ''
    CYAN = '\033[96m' if args.colour else ''
    BLUE = '\033[94m' if args.colour else ''
    GREEN = '\033[92m' if args.colour else ''
    YELLOW = '\033[93m' if args.colour else ''
    RED = '\033[91m' if args.colour else ''
    GREY = '\033[38;5;246m' if args.colour else ''
    BOLD = '\033[;1m' if args.colour else ''
    END = '\033[0m' if args.colour else ''
    ORANGE = '\033[38;5;208m' if args.colour else ''
