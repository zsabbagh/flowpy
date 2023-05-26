from flowpy.main import FlowPy
from flowpy.errors import *

def test_implicit_flow():
    flowpy = FlowPy("""
# fp a: my_label.
def alpha():
    if a == 1:
        print()
    else:
        return 0
    """)
    result = flowpy.run()
    print(result)
    assert len(result) == 1
    assert type(result[0])==ImplicitFlowError

def test_explicit_flow():
    flowpy = FlowPy("""
# fp a: high.
a = 1
b = a
    """)
    result = flowpy.run()
    print(result)
    assert len(result) == 1
    assert type(result[0])==ExplicitFlowError
    assert result[0].var_from.name == "a"
    assert result[0].var_to.name == "b"