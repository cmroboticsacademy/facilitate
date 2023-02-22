from parsing.ast import ASTNode

class Visitor:
    def visit(self, astnode:ASTNode):
        pass


def overrides(interface_class):
    def overrider(method):
        assert(method.__name__ in dir(interface_class))
        return method
    return overrider