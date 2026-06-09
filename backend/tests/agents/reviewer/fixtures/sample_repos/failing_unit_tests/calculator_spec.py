# Reference assertions for the seeded bugs (named *_spec.py so the host pytest
# does NOT collect it — only the in-sandbox runner executes it).
from calculator import add, multiply


def check() -> None:
    assert add(2, 2) == 4
    assert multiply(3, 4) == 12
