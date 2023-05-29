from flowpy.state import State

def test_rule_parsing():
    """
    Test that the rule parsing works as expected.
    """
    state = State()
    state.add_rules("a: my_label, my_label_2. b: other_label")
    print(state.get_labels("b"))
    print(state.get_labels("a"))
    print(state.get_labels("b"))
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


def test_unit_rule():
    """
    Test that unit rules work as expected.
    """
    state = State()
    state.add_rules("a: (), label. b: ().")
    assert state.get_labels("a") == {"label"}
    assert state.get_labels("b") == set()
    state.add_rules("*: ()")
    assert state.get_labels("a") == set()
    assert state.get_labels("b") == set()


def test_rule_order():
    """
    Test that labels are applied in the order they are given.
    Unit rules should be applied first and take precedence.
    """
    state = State()
    state.add_rules("a: label.")
    assert state.get_labels("a") == {"label"}
    state.add_rules("a*: label2.")
    assert state.get_labels("a") == {"label", "label2"}
    state.add_rules("*: ().")
    assert state.get_labels("a") == set()


def test_copy_state():
    """
    Tests that copying a state works as expected.
    Deepcopy is used to avoid modifying the original state.
    """
    state = State()
    state.add_rules("a: label.")
    assert state.get_labels("a") == {"label"}
    state2 = state.copy()
    state.add_rules("a*: label2.")
    assert state.get_labels("a") == {"label", "label2"}
    assert state2.get_labels("a") == {"label"}
    state2.add_rules("a*: label3.")
    assert state.get_labels("a") == {"label", "label2"}
    assert state2.get_labels("a") == {"label", "label3"}

def test_combine():
    """
    Tests that combining states works as expected.
    """
    state = State()
    state.add_rules("a: label.")
    state2 = State()
    state2.add_rules("a: label2.")
    state.combine(state2)
    assert state.get_labels("a") == {"label", "label2"}
    assert state2.get_labels("a") == {"label2"}
