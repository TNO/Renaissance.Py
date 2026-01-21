# Renaissance Experiments

This project is experimental in nature and aims to explore various concepts and techniques to apply renaissance pattern matching in a generic way using multiple abract syntax trees. 

The code for the experiments is located in the [python](./python) folder.

ADR:
use python sytle of meta programming to navigate through the children _'fields' and '_attributes' instead of get_children() _getchildren() _children
e.g.

```
class IfAstNode():
    _fields = (
        'test',
        'body',
        'else',
    )
```

instead of
```python
class IfAstNode():
    _Children = [
         ImplicitNode(test,[AstNode]  ) 
         ImplicitNode(body,[AstNode]  )
         ImplicitNode(orelse.[AstNode]) 
                ]
```