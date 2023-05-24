from ..flowpy import FlowPy

def test_flowpy():
    flowpy = FlowPy("""
    # fp a: my_label.
    def alpha():
        if a == 1:
            return 1
        else:
            return 0
    """)
    result = flowpy.run()
    assert not result