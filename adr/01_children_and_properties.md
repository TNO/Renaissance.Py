#

description: This document explains the design decision to have all AST nodes contain both children and properties.

all ast nodes should have children and properties. This is a fundamental design decision that allows us to
represent complex structures in a consistent way. Children are the nodes that are directly connected to a parent node, while properties are the attributes that describe the node itself. By having both children and properties, we can create a rich and flexible representation of our data that can be easily traversed and manipulated. This design also allows us to maintain a clear separation between the structure of our data and the information it contains, making it easier to understand and work with.
