import re
from typing import Sequence

from renaissance.syntax_tree import ASTNode, ASTShower, PatternMatch

VERBOSE = False
def to_string(d:dict[str, Sequence[ASTNode]]):
    return {k: [compress(v.text if isinstance(v, ASTNode) else v) for v in vs] for k, vs in d.items()}

def compress(s:str):
    skip_whitespace =  re.sub(r'\s+', ' ',s.replace('\n',''))
    skip_whitespace = re.sub(r'(\W)\s', r'\1',skip_whitespace)
    skip_whitespace = re.sub(r'\s(\W)', r'\1',skip_whitespace)
    return skip_whitespace.strip()

def show_node(node: ASTNode, title:str = ''):
    if VERBOSE:
        if title:
            print(f'\n{"="*10} {title} {"="*10}')
        ASTShower.show_node(node)

def debug_mismatch(debug_mismatches, atu, patterns: list[ASTNode], matches: list[PatternMatch]):
    if debug_mismatches:
        for idx, pattern in enumerate(patterns):
            show_node(pattern, f"Pattern[{idx}]")
        show_node(atu, "CPP code")

        for match in matches:
            print(f'\nmatch({[compress(p.text) for p in match.patterns]})' + '{')
            print(f"  start node: {compress(match.nodes[0].text)}")
            for k, vs in match.expansions.items():
                # right align the key
                print(f"{k.rjust(12)}: {[compress(v.text) for v in vs]}")
            print('}')
        print('    expected dict should look like:')
        print(f'      {[to_string(match.expansions) for match in matches]}')
