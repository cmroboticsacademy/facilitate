from analyzers.visitor import Visitor, overrides
from parsing.ast import ASTNode

class BlockIdListVisitor(Visitor):
    def __init__(self):
        self.statement_list = []

    @overrides(Visitor)
    def visit(self, astnode:ASTNode):
        self.statement_list.append(astnode.blockid)

class NodeListVisitor(Visitor):
    def __init__(self):
        self.statement_list = []

    @overrides(Visitor)
    def visit(self, astnode:ASTNode):
        self.statement_list.append(astnode)
