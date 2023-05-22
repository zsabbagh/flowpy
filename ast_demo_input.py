#fp foo: highlabel. bar: lowlabel
def main():
    foo = 1
    bar = 0
    print("Hello world")
    if foo:
        bar = foo
        # print("LEAKED!!!!")
    elif bar == 0:
        foo = bar
        # print("sdofnrwö")
    else:
        print("testing how this looks in the ast")

    # Complex assignment (not yet implemented)
    # low, temp, something = 1, 2, 3


def function_that_will_not_be_evaluated():
    pass
