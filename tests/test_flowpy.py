from flowpy.main import FlowPy
from flowpy.errors import *

def test_implicit_flow_function():
    flowpy = FlowPy("""
# fp a: my_label.
def alpha():
    if a == 1:
        print()
    else:
        return 0
    """)
    result = flowpy.run()
    assert len(result) == 1
    assert type(result[0])==ImplicitFlowError
    assert result[0].line == 5
    assert result[0].pc == {'my_label'}
    assert result[0].var_to.labels is None

def test_implicit_flow_assignment():
    flowpy = FlowPy("""
# fp a: my_label.
if a == 1:
    b = 1
else:
    b = 1
""")
    result = flowpy.run()
    assert len(result) == 2
    assert type(result[0]) == ImplicitFlowError
    assert result[0].line == 4
    assert result[0].pc == {'my_label'}
    assert result[0].var_to.name == 'b'
    assert type(result[1]) == ImplicitFlowError
    assert result[1].line == 6
    assert result[1].pc == {'my_label'}
    assert result[1].var_to.name == 'b'
    assert result[1].var_to.labels == set()

def test_explicit_flow_assignment():
    """
    Test that explicit flows are detected
    during assignment.
    """
    flowpy = FlowPy("""
# fp a: high.
a = 1
b = a
    """)
    result = flowpy.run()
    assert len(result) == 1
    assert type(result[0])==ExplicitFlowError
    assert result[0].var_from.name == "a"
    assert result[0].var_from.labels == {'high'}
    assert result[0].var_to.name == "b"
    assert result[0].var_to.labels == set()

def test_explicit_flow_nested():
    """
    Test that explicit flows are detected
    during nested ifs
    """
    flowpy = FlowPy("""
# fp a: high.
a = 1
b = 2
if b:
    b = b + 1
    if b + 1:
        b = a
    """)
    result = flowpy.run()
    assert len(result) == 1
    assert type(result[0])==ExplicitFlowError
    assert result[0].var_from.name == "a"
    assert result[0].var_from.labels == {'high'}
    assert result[0].var_to.name == "b"
    assert result[0].var_to.labels == set()

def test_implicit_flow_nested():
    """
    Test that explicit flows are detected
    when there exists a nested function definition
    and nested ifs.
    """
    flowpy = FlowPy("""
# fp a: high.
a = 2
# fp b: low.
def foo():
    def bar():
        if a == 2:
            b = 1
            if b:
                a = 10
        else:
            b = 2
""")
    result = flowpy.run()
    assert len(result) == 3
    assert type(result[0])==ImplicitFlowError
    assert result[0].pc == {'high'}
    assert result[0].var_to.labels == {'low'}
    assert type(result[1])==ImplicitFlowError

