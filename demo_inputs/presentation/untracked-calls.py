# Current limitation:
# does not track the labels of a variable
# through function calls.

# fp a: high.
def check_correct(a):
    if a > 0:
        print("a is positive")
# fp secret: superhigh.
secret = 42
check_correct(secret)