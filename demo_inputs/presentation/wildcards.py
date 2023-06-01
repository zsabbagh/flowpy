# fp s*ret: high.
secret = "a secret value"
silver_egret = secret # NOT caught
public_variable = None
if silver_egret == "a secret value":
    public_variable = 1