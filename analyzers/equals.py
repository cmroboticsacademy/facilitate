from visitor import Visitor, overrides

class Equals(Visitor):

    @overrides(Visitor)
    def visit(self, astnode:ASTNode):
        pass

    def equals(node1: ASTNode, node2: ASTNode) -> bool:
        
        pass