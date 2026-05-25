BASIS = [
    ("AND", 2, lambda a, b: a and b),
    # ("OR", 2, lambda a, b: a or b),
    # ("NAND", 2, lambda a, b: not (a and b)),
    ("NOR", 2, lambda a, b: not (a or b)),
]
