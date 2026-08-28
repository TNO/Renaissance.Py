# Navigation

{ #feature-navigation }

**Stable ID:** `FEATURE-NAVIGATION`

## MISC

Navigate the AST based on

* AST structure, e.g., get the parent, ancestors, children, descendants, or siblings of an AST node.
* Usage, e.g., from reference to [fully qualified name of] definition, from reference to (forward) declaration, from definition to all references.
  * (probably) limited to current file, as not all ASTs of all files might fit into memory
* Inheritance, from base class to all derived classes, from derived class to (all) base class(es).

1. Navigation
      1. parent, ancestors, children, descendants
      1. siblings
      1. Usage - definition / (forward) declaration - references (ONLY in current file / analysis unit)
      1. Inheritance - base / derived class
