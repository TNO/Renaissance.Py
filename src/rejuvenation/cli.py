import sys
from pathlib import Path

from renaissance.impl.python import PythonASTNode
from renaissance.refactoring.unit2pytest import convert_pytest
from renaissance.syntax_tree import ASTFactory, ASTShower

factory = ASTFactory(PythonASTNode, [])


def convert(taut):
    taut_atu = factory.create(taut)
    result = convert(taut_atu)
    if result.has_changes:
        with open(taut, 'w') as f:
            f.write(result.apply_to_string())


def refactor(taut):
    for taut in dir(sys.argv[1]):
        convert(taut)


# def refactor():
#     factory = ASTFactory(PythonASTNode, [])
#     for taut in dir(sys.argv[1]):
#         taut_atu = factory.create(taut)
#         result = convert(taut_atu)
#         if result:
#             with open(taut, 'w') as f:
#                 f.write(result)

def select_pyton_file():

    # is_python_file = lambda file_path: file_path.is_file() and file_path.suffix.lower() == '.py'
    current_dir = Path('.')
    print(f'refactor in {current_dir.resolve()}')

    return current_dir.glob('**/*test_c_match_finder.py')
    # return (file_path for file_path in current_dir.iterdir() if is_python_file)




if __name__ == "__main__":
    sample = factory.create('c_cpp/test_c_match_finder.py')
    # ASTShower.show_node(sample)

    for file in select_pyton_file():
        # print(file.resolve())
        convert_pytest(file)