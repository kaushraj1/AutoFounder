"""Seeded logic bugs — the self-healer must fix THIS file, not the spec."""


def add(a: int, b: int) -> int:
    return a + b + 1  # BUG: off-by-one


def multiply(a: int, b: int) -> int:
    return a + b  # BUG: should be a * b
