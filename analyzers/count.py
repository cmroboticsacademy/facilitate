from analyzers.visitor import Visitor, overrides
from parsing.ast import ASTNode

class CountVisitor(Visitor):
    def __init__(self):
        self.counter = 0

    @overrides(Visitor)
    def visit(self, astnode:ASTNode):
        self.counter += 1