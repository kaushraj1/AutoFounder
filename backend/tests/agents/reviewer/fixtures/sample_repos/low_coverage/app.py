"""Passing code, but most branches are untested (coverage ~62%)."""


def classify(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def covered() -> str:
    return classify(95)
