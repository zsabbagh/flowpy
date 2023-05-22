from ..state import State

def test_rule_parsing():
    """
    Test that the rule parsing works as expected.
    """
    state = State()
    state.add_rules("a: my_label, my_label_2. b: other_label")
    assert state.get_labels("a") == {"my_label", "my_label_2"}
    assert state.get_labels("b") == {"other_label"}

def test_wildcards():
    """
    Test that the wildcard rules work as expected.
    """
    state = State()
    state.add_rules("a*: my_label, my_label_2. b: other_label")
    assert state.get_labels("a") == {"my_label", "my_label_2"}
    assert state.get_labels("another_variable") == {"my_label", "my_label_2"}
    assert state.get_labels("b") == {"other_label"}

def test_wildcards_with_ending():
    """
    Test that the wildcard rules work as expected.
    """
    state = State()
    state.add_rules("a*ble: my_label, my_label_2. b: other_label")
    assert state.get_labels("a") == set()
    assert state.get_labels("another_var") == set()
    assert state.get_labels("acceptable") == set(["my_label", "my_label_2"])
    assert state.get_labels("b") == {"other_label"}

def test_rules_with_no_labels():
    """
    Test rules with no labels.
    """
    state = State()
    state.add_rules("a*: . b*: other_label")
    assert state.get_labels("a_should_be_empty") == set()
    assert state.get_labels("should_be_empty") == set()
    assert state.get_labels("should_also_be_empty") == set()
    assert state.get_labels("b_should_not_be_empty") == {"other_label"}

def test_pure_wildcards():
    """
    Test that pure wildcards work as expected.
    """
    state = State()
    state.add_rules("*: a, b, c, d, e.")
    assert state.get_labels("/weird/Li::nE") == {"a", "b", "c", "d", "e"}
    assert state.get_labels("foo") == {"a", "b", "c", "d", "e"}
    assert state.get_labels("bar") == {"a", "b", "c", "d", "e"}
    assert state.get_labels("baz") == {"a", "b", "c", "d", "e"}