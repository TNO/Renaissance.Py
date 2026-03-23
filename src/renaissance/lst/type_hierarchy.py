
class Base:
    pass
class Expression(Base):
    pass
class Statement(Base):
    pass
class Declaration(Statement):
    pass
class Base:
    pass
class Function:
    pass
class If:
    pass
class While:
    pass
class For:
    pass
class Unary:
    pass
class Binary:
    pass
class Trinary:
    pass
class Assignment:
    pass
class Other:
    def __init__(self,kind):
        self.kind = kind

