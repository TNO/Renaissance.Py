{ #dev-architecture-code }
# Code architecture

**Stable ID:** `ARCH-CODE`

1. We have chosen [Python](https://www.python.org/) as the programming language for our implementation. 


    a. We have chosen the latest released version, currently 3.14, and when a new version is released we intend to follow within three months, given that resources permit.
    
    b. We have chosen to use [typing](https://docs.python.org/3/library/typing.html) on all functions and their parameters.
   
    c. Our code should adhere to the conventions of Python, such as [philosophy](https://peps.python.org/pep-0020/), [style](https://peps.python.org/pep-0008/), and [documentation](https://peps.python.org/pep-0257/).
    
1. We defined AST Node as a [Protocol (a.k.a. statically duck typing)](https://typing.python.org/en/latest/spec/protocol.html), with basic functionality and a back door: `get_original_node` to obtain the AST node as provided by the parser.

1. AST Nodes are read only and immutable.

1. AST Nodes are navigable, so parent must be present (except for the ATU / top node) and children are always present (although it might be an empty list).  

1. Standard 'semantic' functions must be provided that when given a code snippet will return the variables read or  written. Based on the output of these functions dependencies between code snippets are determined.

1. We enable syntax pattern matching and semantic filtering. 
In most cases, standard functions (as describe before) are enough, but we enable user specific filter functions that access the original AST. 

1. We collect multiple transformations, we are syntax aware - to handle shared text boundaries, and then in one step transform the code text.
