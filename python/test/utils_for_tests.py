import re
from typing import Sequence
from syntax_tree.ast_node import ASTNode
from syntax_tree.ast_shower import ASTShower


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
