import uuid
from voluptuous.error import Error


def UUID(value):
    """Checks UUID"""
    return uuid.UUID(value)


def NotNone(msg=None):
    """Checks that value is not None neither empty string"""
    def f(v):
        if v is not None:
            if type(v) == str:
                if v == '':
                    raise Error(msg or "value must be not empty")
                else:
                    return v
            return v
        else:
            raise Error(msg or "value must be not None")
    return f
