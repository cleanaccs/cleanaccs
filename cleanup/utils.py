from functools import reduce


def first_not_null(*args):
    for arg in args:
        if arg is not None:
            return arg
    return None


def getattrd(obj, name, default=None):
    try:
        return reduce(getattr, name.split("."), obj)
    except AttributeError as e:
        return first_not_null(default, None)
