# fp secret: high.
secret = [1, 2, 3, 4, 5]
public_value = 0
for i in secret:
    public_value = 1
    if i > 4:
        print("secret has values higher than 4")