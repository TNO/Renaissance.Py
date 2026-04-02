from ast import AST
from typing import Any

"""
implementation that patches the native ast using 'traits' mechanism,
require minimum amound of code to make the matcher work
 
"""



def is_part_of_translation_unit(_: AST):
    return True


AST.is_part_of_translation_unit = is_part_of_translation_unit


