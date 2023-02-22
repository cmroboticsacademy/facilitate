from parsing.ast import ASTNode
from collections import defaultdict, Counter
from collections.abc import Callable
from queue import PriorityQueue


def get_max_key(pq:defaultdict)->int:
    return max(pq.keys())

def insert_pq(pq:defaultdict, n:ASTNode):
    pq[n.height()].append(n)
    
def dice(parent1:ASTNode, parent2:ASTNode, mappings: list):
    desc1 = parent1.get_descendants()
    desc2 = parent2.get_descendants()
    
    contained_mappings = [(t1, t2) for (t1, t2) in mappings                           if (t1 in desc1 and t2 in desc2)]
    return 2*len(contained_mappings) / (len(desc1) + len(desc2))
    

def gumtree(head1:ASTNode, head2:ASTNode):
    # top down phase
    subtree_queue1 = defaultdict(list) # dict { height : [subtrees with that height]
    subtree_queue2 = defaultdict(list)
    
    candidate_mappings = []
    mappings = []
    
    
    insert_pq(subtree_queue1, head1)
    insert_pq(subtree_queue2, head2)
    
    while len(subtree_queue1)> 0 and len(subtree_queue2) > 0:
        maxheight1 = get_max_key(subtree_queue1)
        maxheight2 = get_max_key(subtree_queue2)
        
        if maxheight1 != maxheight2:
            if maxheight1 > maxheight2:
                maxtrees = subtree_queue1[maxheight1]
                del subtree_queue1[maxheight1]
                for t in maxtrees:
                    for c in t.children:
                        insert_pq(subtree_queue1, c)
            else:
                maxtrees = subtree_queue2[maxheight2]
                del subtree_queue2[maxheight2]
                for t in maxtrees:
                    for c in t.children:
                        insert_pq(subtree_queue2, c)
        else:
            maxtrees1 = subtree_queue1[maxheight1]
            maxtrees2 = subtree_queue2[maxheight2]
            added_trees1 = []
            added_trees2 = []
            for t1 in maxtrees1:
                for t2 in maxtrees2:
                    if t1 == t2:
                        if head1.count_subtree_occurences(t2) > 1 or                         head2.count_subtree_occurences(t1) > 1:
                            candidate_mappings.append((t1, t2))
                        else:
                            mappings.append((t1, t2))
                        added_trees1.append(t1)
                        added_trees2.append(t2)
            for t in maxtrees1:
                if t not in added_trees1:
                    for c in t.children:
                        insert_pq(subtree_queue1, c)
            for t in maxtrees2:
                if t not in added_trees2:
                    for c in t.children:
                        insert_pq(subtree_queue2, c)
    sorted_candidates = sorted(candidate_mappings, 
                               key = lambda t1, t2: dice(t1.parent, t2.parent, mappings),
                               reverse=True)
    while len(sorted_candidates) > 0:
        top = sorted_candidates[0]
        del sorted_candidates[0]
        mappings.append(top)
        sorted_candidates = [s for s in sorted_candidates                              if s[0]!=top[0] and s[1] != top[1]]
    
    # bottom up
    matched1 = [t[0] for t in mappings]
    matched2 = [t[1] for t in mappings]
    def bottom_up_helper(node:ASTNode):
        if node not in matched1:
            mapped_child = False
            for c in node.children:
                if c in matched1:
                    mapped_child = True
                    break
            if mapped_child:
                candidates = []
                head2.accept(lambda n : 
                             n.op == node.op and n.blockid == node.blockid and n not in matched2 and candidates.append(n))
                candidates = sorted(candidates,
                                    key = lambda t2: dice(node, t2, mappings),
                                    reverse=True)
                if len(candidates) > 0 and dice(node, candidates[0], mappings) > 0.45:
                    mappings.append(node, candidates[0])
                    # here the original gumtree algorithm uses an edit script algorithm to find 
                    # further mappings for trees under a certain size, but all these programs are small
                    # so I don't anticipate needing that
    node1.accept_postorder(bottom_up_helper)
    return mappings
