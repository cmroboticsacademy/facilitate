class ASTNode:
    def __init__(self):
        self.parent = None
        self.blockid = None
        self.op = None
        self.children = []
        self._height = 1
        
    def __init__(self, parent, blockid, desc, children):
        self.parent = parent
        self.blockid = blockid
        self.op = desc
        self.children = sorted(children, key=lambda n: n.blockid)
        self._height = self.__height__()
    
    def accept(self, visit_func:Callable[['ASTNode'],None]):
        visit_func(self)
        for c in self.children:
            c.accept(visit_func)
            
    def accept_postorder(self, visit_func:Callable[['ASTNode'],None]):
        for c in self.children:
            c.accept(visit_func)
        visit_func(self)
            
    def __eq__(self, other:'ASTNode'):
        if self.blockid != other.blockid or self.op != other.op:
            return False
        if len(self.children) != len(other.children):
            return False
        return self.children == other.children
    
    def __height__(self):
        if len(self.children) == 0:
            return 1
        return max([c.height() for c in self.children]) + 1
    
    def height(self):
        return self._height
    
    def count_subtree_occurences(self, other:'ASTNode'):
        if other._height > self._height:
            return 0
        if self == other:
            return 1
        counter = 0
        for c in self.children:
            counter += c.count_subtree_occurences(other)
        return counter
        
    def iter_descendants(self):
        yield self
        for c in self.children:
            yield from c.iter_descendants()
            
    def get_descendants(self):
        return [s for s in self.iter_descendants()]
    
    def __str__(self):
        return f"ASTNode: {self.blockid} {self.op}\n\tParent: {self.parent.blockid if self.parent else None}, {len(self.children)} children"
