from parsimonious.grammar import Grammar

grammar = Grammar(
    """
    label = ~"[_A-Z0-9a-z]*"
    """
)
with open("file.py") as f:
    text = f.read().rstrip()
    g = grammar.parse(text)
    print(g)
