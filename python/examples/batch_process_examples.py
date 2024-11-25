#use clang to load and walk a compilation database

from dataclasses import dataclass
from typing_extensions import Iterable, override
from impl import ClangASTNode, ClangJsonASTNode
from refactoring import CleanupRefactoring
from syntax_tree import ASTProcessor, ASTNode, ASTNodeType, TextUtils, ASTFactory, BatchASTProcessor

example_1 = TextUtils.strip_indent("""
        void x(int a) {
        }
        void f1(){
            int unused = 0;
            int unused2 = 0; //must be removed
            if (a==1) {
                int unused = 0;
                int unused2 = 0; //should be kept
                int c = unused2;
                x1(c);
            }
        }
        """)

example_2 = TextUtils.strip_indent("""
        void x(int a) {
        }
        void f2(){
            int unused = 0;
            if (a==1) {
                int unused = 0;
                int another_unused = 0;
                int used2 = 0; //should be kept
                int c = used2;
                x2(c);
            }
        }
        """)

# generate a simple code base provider in real life use a compilation database
def simple_codebase_provider() -> Iterable[tuple[ASTFactory[ASTNodeType], ASTNodeType]]:
    for impl_type in [ClangASTNode, ClangJsonASTNode]:
        factory = ASTFactory(impl_type)
        atu1 = factory.create_from_text(example_1, impl_type.__name__+'1.c')
        yield factory, atu1
        atu2 = factory.create_from_text(example_2, impl_type.__name__+'2.c')
        yield factory, atu2

def print_results(title, batch_processor):
    print(title +':')
    for file, code in batch_processor.in_memory_files.items():
        print(TextUtils.shift_right(file, 4)+'\n')
        print(TextUtils.shift_right(code, 8)+'\n')


def batch_remove_unused_variable_once_example():
    """
    This function demonstrates a batch processing example using different AST node implementations.
    It iterates over a list of AST node implementations (`ClangASTNode` and `ClangJsonASTNode`), 
    and for each implementation, it generates a codebase provider that yields tuples of 
    `ASTFactory` and `ASTNode` created from example source texts (`example_1` and `example_2`).
    The function then creates a `BatchASTProcessor` with in-memory storage enabled and processes 
    the codebase using the `CleanupRefactoring.remove_unused_variables` refactoring operation.
    Finally, it prints the rewritten code stored in memory.
    """
    #generate a batch processor for testing purposes we store into memory
    batch_processor = BatchASTProcessor(in_memory=True)
    batch_processor.once(simple_codebase_provider, CleanupRefactoring.remove_unused_variables)
    #print the rewritten code normally you would write to a file
    print_results('example batch remove unused variable once', batch_processor)


def batch_repeat_example():
    """
    Demonstrates the use of a batch processor to perform multiple refactoring operations on a codebase.
    This example creates an in-memory batch processor and applies two refactoring operations:
    1. CleanupRefactoring.remove_unused_variables: Removes unused variables from the codebase.
    2. remove_function: Removes all function calls from the codebase.
    The results of the refactoring operations are printed to the console.

    Repeat is in action here: 
        the first time the codebase is processed, the unused variables are removed.
        and the function calls are removed.
        the second time the codebase is processed, the new unused variables are removed again.
    Note:
        In a real-world scenario, the rewritten code would typically be written to a file instead of being printed.
    """
    #generate a batch processor for testing purposes we store into memory
    batch_processor = BatchASTProcessor(in_memory=True)
    #remove a function to create more unused variables
    def remove_function(ast_processor: ASTProcessor[ASTNodeType]):
        ast_processor.find_kind('(?i)Call_?Expr').\
            for_each(lambda node: ast_processor.insert_before( '// ', node, False, False ))
        
    # batch_processor.repeat(simple_codebase_provider, [remove_function])   
    batch_processor.repeat(simple_codebase_provider, [CleanupRefactoring.remove_unused_variables, remove_function])   
    #print the rewritten code normally you would write to a file
    print_results('example batch repeat', batch_processor)

@dataclass
class Call:
    callee: str
    calls: str

@dataclass
class Calls(list[Call], BatchASTProcessor.HasFinalAction):
    @override
    def final_action(self):
        print('example batch analysis:\n')
        print('Calls:')
        for call in self:
            print('    '+call.callee + ' --  calls --> ' + call.calls)

def batch_analysis_example():
    """
    Example function demonstrating analysis of AST nodes.
    This function creates a batch processor that processes AST nodes in memory.
    It defines a `Call` dataclass to represent function calls and a `Calls` dataclass
    to store a list of `Call` instances. The function `add_function_call` adds a function
    call to the `Calls` list, and `store_function_call` processes AST nodes to find
    function call expressions and store them.
    The batch processor runs the `store_function_call` function on a simple codebase
    provider and prints the collected function calls.
    
    Note that instead of an find_kind also a visitor could be used. 
    See the ASTNode process method for more information.

    """
    #generate a batch processor for testing purposes we store into memory
    with BatchASTProcessor(in_memory=True) as batch_processor:
    #remove a function to create more unused variables

        def add_function_call(call: ASTNode, calls: Calls):
            callee = call.get_ancestor('(?i)Function_?Decl')
            if callee:
                calls.append(Call(callee.get_name(), call.get_children()[0].get_name()))
        

        def store_function_call(ast_processor: ASTProcessor[ASTNodeType]):
            calls = ast_processor.user_object(str(Calls), Calls)
            ast_processor.find_kind('(?i)Call_?Expr').\
                for_each(lambda node: add_function_call(node, calls))

            
        batch_processor.once(simple_codebase_provider, store_function_call)   


if __name__ == "__main__":
    # a list of example to show batch processing of a code base
    batch_remove_unused_variable_once_example()
    batch_repeat_example()
    batch_analysis_example()