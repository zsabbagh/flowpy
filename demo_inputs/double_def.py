# fp a: label.
def foo():
    a = 1
    # fp *: label2.
    def bar():
        b = 2
        c = 3
        if a:
            c = 4
        return c
    return bar()
