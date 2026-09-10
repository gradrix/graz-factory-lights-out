def chosen_value(value: int = 42) -> int:
    if isinstance(value, bool):
        raise TypeError("bool is not a valid input")
    if type(value) is not int:
        raise TypeError("only built-in integers are accepted")
    return max(0, min(100, value))
