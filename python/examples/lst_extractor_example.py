from lst.lst import LSTNode
from matchers.pattern_matcher import StructuralPatternMatcher, MatchResult


def dummy_example():
    # Construct a fake pattern tree manually
    cond = LSTNode(node_type="$cond", properties={}, signature="", offset=0)
    body = LSTNode(node_type="$body", properties={}, signature="", offset=0)
    if_node = LSTNode(
        node_type="if_statement",
        properties={},
        signature="if x > 0: print(x)",
        offset=0,
    )
    if_node.add_child(cond)
    if_node.add_child(body)

    # Now imagine we match against an actual AST built from real code
    matcher = StructuralPatternMatcher(if_node)
    fake_root = LSTNode("if_statement", {}, "if x > 0: print(x)", 0)
    fake_root.add_child(LSTNode("binary_expression", {}, "x > 0", 0))
    fake_root.add_child(LSTNode("call_expression", {}, "print(x)", 0))

    results = matcher.match(fake_root)
    for match in results:
        print(match)


if __name__ == "__main__":
    dummy_example()
