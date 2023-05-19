#fp high: my_label. low: other_label
def main():
    high = 1
    low = 0
    print("Hello world")
    if high:
        low = high
        #print("LEAKED!!!!")
    elif low == 0:
        high = low
        #print("sdofnrwö")
    else:
        print("testing how this looks in the ast")

    # Complex assignment (not yet implemented)
    # low, temp, something = 1, 2, 3

def function_that_will_not_be_evaluated():
    pass
