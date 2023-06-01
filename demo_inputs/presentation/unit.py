# Unit labels take precedence over other rules.
# All variables have empty labels by default.
# Explicitly stating empty labels should
# therefore override any other rules.

# fp secret: high.
# fp s*: superhigh. secret: ().
secret = 1
if secret:
    print()
some_other_secret = 2
if some_other_secret:
    print()