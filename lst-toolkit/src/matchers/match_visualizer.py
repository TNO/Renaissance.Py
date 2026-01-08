from matchers.match import Match
from termcolor import colored


def highlight_match(code: str, match: Match) -> str:
    lines = code.splitlines(keepends=True)
    highlights = []

    for name, nodes in match._result.bindings.items():
        for node in nodes:
            start = node.offset
            end = node.offset + len(node.signature)
            highlights.append((start, end, name))

    highlights.sort()
    out = ""
    i = 0
    for start, end, label in highlights:
        out += code[i:start]
        out += colored(code[start:end], "red", attrs=["bold"]) + f"/*${label}*/"
        i = end
    out += code[i:]
    return out
