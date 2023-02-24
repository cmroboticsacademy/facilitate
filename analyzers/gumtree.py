from parsing.ast import ASTNode
from collections import defaultdict, Counter
from queue import PriorityQueue
from analyzers.statementlistvisitor import NodeListVisitor


def get_max_key(pq:defaultdict)->int:
    return max(pq.keys())

def insert_pq(pq:defaultdict, n:ASTNode):
    pq[n.height()].append(n)
    
def dice(parent1:ASTNode, parent2:ASTNode, mappings: list):
    desc1 = parent1.get_descendants()
    desc2 = parent2.get_descendants()
    
    contained_mappings = [(t1, t2) for (t1, t2) in mappings                           if (t1 in desc1 and t2 in desc2)]
    return 2*len(contained_mappings) / (len(desc1) + len(desc2))

def generate_similarity_matrix(head1:ASTNode, head2:ASTNode):
    ids_visitor_1 = NodeListVisitor()
    ids_visitor_2 = NodeListVisitor()
    head1.accept(ids_visitor_1.visit)
    head2.accept(ids_visitor_2.visit)

    matrix = [ 
            [ 
                False 
                for _ in range(len(ids_visitor_2.statement_list)) 
            ] 
            for _ in range(len(ids_visitor_1.statement_list)) 
        ]
    
    for i, node1 in enumerate(ids_visitor_1.statement_list):
        for j, node2 in enumerate(ids_visitor_2.statement_list):
            matrix[i][j] = node1.node_equals(node2)
    
    return matrix, ids_visitor_1.statement_list, ids_visitor_2.statement_list

def sim_matrix_count_subtree_occurrences(target_node_index, sim_matrix, count_in_tree1=True):
    count = 0
    if count_in_tree1: # count occurences of target node in tree 1
        for i in range(len(sim_matrix)):
            if sim_matrix[i][target_node_index]:
                count += 1
    else: # count occurences of target node in tree 2
        for i in range(len(sim_matrix[0])):
            if sim_matrix[target_node_index][i]:
                count += 1
    return count
    

# @profile
def gumtree(head1:ASTNode, head2:ASTNode):
    # generate similarity matrix to optimize comparisons later
    sim_matrix, nodeslist1, nodeslist2 = generate_similarity_matrix(head1, head2)
    nodes_dict1 = {n:i for i, n in enumerate(nodeslist1)}
    nodes_dict2 = {n:i for i, n in enumerate(nodeslist2)}

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
            added_trees1 = set()
            added_trees2 = set()
            for t1 in maxtrees1:
                for t2 in maxtrees2:
                    if t1.node_equals(t2):
                        head1_occurences = sim_matrix_count_subtree_occurrences(nodes_dict2[t2], sim_matrix, count_in_tree1=True)
                        head2_occurences = sim_matrix_count_subtree_occurrences(nodes_dict1[t1], sim_matrix, count_in_tree1=False)
                        if head1_occurences > 1 or head2_occurences > 1:
                            candidate_mappings.append((t1, t2))
                        else:
                            mappings.append((t1, t2))
                        added_trees1.add(t1)
                        added_trees2.add(t2)
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
        sorted_candidates = [s for s in sorted_candidates if s[0]!=top[0] and s[1] != top[1]]
    
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
                             n.op == node.op and n not in matched2 and candidates.append(n))
                candidates = sorted(candidates,
                                    key = lambda t2: dice(node, t2, mappings),
                                    reverse=True)
                if len(candidates) > 0 and dice(node, candidates[0], mappings) > 0.45:
                    mappings.append(node, candidates[0])
                    # here the original gumtree algorithm uses an edit script algorithm to find 
                    # further mappings for trees under a certain size, but all these programs are small
                    # so I don't anticipate needing that
    head1.accept_postorder(bottom_up_helper)
    return mappings
