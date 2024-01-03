from parsing.ast import ASTNode
from collections import defaultdict
from queue import PriorityQueue
from analyzers.statementlistvisitor import NodeListVisitor


def get_max_key(pq:defaultdict)->int:
    return max(pq.keys())

def insert_pq(pq:defaultdict, n:ASTNode):
    pq[n.height()].add(n)

def dice(parent1:ASTNode, parent2:ASTNode, mappings: list):
    desc1 = parent1.get_descendants()
    desc2 = parent2.get_descendants()

    contained_mappings = []
    for (t1, t2) in mappings:
        t1_contain = False
        for n in desc1:
            if n.subtree_equals(t1):
                t1_contain = True
        t2_contain = False
        for n in desc2:
            if n.subtree_equals(t2):
                t2_contain = True
        if t1_contain and t2_contain:
            contained_mappings.append((t1, t2))

    return (2*len(contained_mappings) / (len(desc1) + len(desc2))) * (2 if parent1.blockid == parent2.blockid else 1)

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
            matrix[i][j] = node1.subtree_equals(node2)

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
    subtree_queue1 = defaultdict(set) # dict { height : [subtrees with that height]
    subtree_queue2 = defaultdict(set)

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
                    if t1.subtree_equals(t2):
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

            del subtree_queue1[maxheight1]
            del subtree_queue2[maxheight2]

    sorted_candidates = sorted(candidate_mappings,
                               key = lambda t: dice(t[0].parent, t[1].parent, mappings),
                               reverse=True)

    while len(sorted_candidates) > 0:
        top = sorted_candidates[0]
        del sorted_candidates[0]
        mappings.append(top)
        sorted_candidates = [s for s in sorted_candidates if s[0]!=top[0] and s[1] != top[1]]

    # mapping all nodes of subtrees
    def add_children_as_mappings(n1, n2):
        if len(n1.children) != len(n2.children):
            raise Exception("nodes are not the same")
        for i in range(len(n1.children)):
            c1 = n1.children[i]
            c2 = n2.children[i]
            if (c1, c2) not in mappings:
                mappings.append((c1, c2))
                add_children_as_mappings(c1, c2)
    for m1, m2 in mappings:
        add_children_as_mappings(m1, m2)


    # bottom up
    matched1 = [t[0] for t in mappings]
    matched2 = [t[1] for t in mappings]
    def bottom_up_helper(node:ASTNode):
        if node not in matched1:
            # print("not matched", node)
            mapped_child = [False]
            def has_mapped_child(node):
                for c in node.children:
                    if c in matched1:
                        # print("found match")
                        mapped_child[0] = True
            node.accept(has_mapped_child)
            if mapped_child[0]:
                candidates = []
                def unmatched(n):
                    if n.op == node.op and n not in matched2:
                        candidates.append(n)
                head2.accept(unmatched)

                # print(candidates)
                candidates = sorted(candidates,
                                    key = lambda t2: dice(node, t2, mappings),
                                    reverse=True)

                if len(candidates) > 0 and dice(node, candidates[0], mappings) > 0.2:
                    mappings.append((node, candidates[0]))
                    # here the original gumtree algorithm uses an edit script algorithm to find
                    # further mappings for trees under a certain size, but all these programs are small
                    # so I don't anticipate needing that
    head1.accept_postorder(bottom_up_helper)
    return mappings


def get_edit_script(tree_before, tree_after):
    mappings = gumtree(tree_before, tree_after)

    if len(mappings) == 0:
        befores = []
        afters = []
    else:
        befores, afters = zip(*mappings)

    deleted = []
    def get_del_nodes(before_node):
        if before_node not in befores:
            deleted.append(before_node)
    tree_before.accept(get_del_nodes)
    # print("\n".join([str(d) for d in deleted]))


    added = []
    def get_add_nodes(after_node):
        if after_node not in afters:
            added.append(after_node)
    tree_after.accept(get_add_nodes)

    moved = [] # todo, inputs and fields technically get moved too, sometimes next but not always ?????
    for before, after in mappings:
        if (before.parent is None) and (after.parent is None):
            continue
        elif (before.parent is None) or (after.parent is None):
            moved.append((before, after))
        elif before.parent.op != after.parent.op:
            if before.parent not in deleted and after.parent not in added:
                if not any([True if (before.parent == m1 or after.parent == m2) else False for m1, m2 in moved ]):
                    moved.append((before, after))

    return added, deleted, moved


def get_chawathe_edit_script(tree_before, tree_after):
    tree_before_copy = tree_before.copy() # this is the one we manipulate to check if the edit script is correct

    tree_before_copy.dump_json("debugging1.json")
    tree_after.dump_json("debugging2.json")

    mappings = gumtree(tree_before_copy, tree_after)

    # for m in mappings:
    #     print(m[0].blockid, m[1].blockid)

    added = []
    moved = []
    deleted = []
    updated = []


    def find_mapping(node, after=True):
        if after:
            node_maps = [(m1, m2) for m1, m2 in mappings if m2 == node]
        else:
            node_maps = [(m1, m2) for m1, m2 in mappings if m1 == node]
        if len(node_maps) > 1:
            for n1, n2 in mappings:
                print(f"{n1.blockid:50} {n2.blockid:50}")
            print(node)
            for n1, n2 in node_maps:
                print(f"{n1.blockid:50} {n2.blockid:50}")
            raise Exception('mappings should be 1 to 1')
        if len(node_maps) == 0:
            if after:
                return None, node
            else:
                return node, None
        return node_maps[0]

    def insert_update_move_align(node):
        parent_before, parent_after = find_mapping(node.parent, after=True)
        before, _ = find_mapping(node, after=True)
        # insertion
        if before is None:
            copied_node = node.copy_no_children()

            copied_node.blockid = copied_node.blockid+"_copy"

            if node in parent_after.next:
                # if parent_before.next:
                #     copied_node.add_child(parent_before.next)
                parent_before.add_child(copied_node)
            elif node in parent_after.inputs:
                parent_before.add_child(copied_node, "inputs")
            else: # node in fields
                parent_before.add_child(copied_node, "fields")
            # print("added", copied_node.blockid)
            # print("added to parent", copied_node.parent.blockid)
            # print()
            added.append(node)
            mappings.append((copied_node, node))
        elif node.parent:
            # TODO: check update here, probably involves seeing if fields/inputs are changed?
            # move
            if parent_before != before.parent:
                moved.append((before, node))

                before.parent.remove_child(before)

                if node in parent_after.next:
                    parent_before.add_child(before)
                elif node in parent_after.inputs:
                    parent_before.add_child(before, "inputs")
                else: # node in fields
                    parent_before.add_child(before, "fields")

                if before.has_descendant(parent_before):
                    # might indicate nodes to be deleted or moved; in any case, separate the parent so that we don't get circles in our tree
                    parent_before.parent.remove_child(parent_before)
            #check alignment in the original program -- we don't do that (unlikely to be a thing)
            # else:

    def breadth_first_traverse(root, apply_fn):
        node_q = []
        node_q.append(root)
        while len(node_q) > 0:
            curr = node_q.pop(0)
            apply_fn(curr)
            node_q.extend(curr.children)

    breadth_first_traverse(tree_after, insert_update_move_align)

    def delete(node):
        _, after = find_mapping(node, after=False)
        if after is None:
            node.parent.remove_child(node)
            deleted.append(node)

    tree_before_copy.accept_postorder(delete)

    from analyzers.count import CountVisitor
    c = CountVisitor()
    try:
        tree_before_copy.accept(c.visit)
    except:
        print(c.counter)

    if (not (tree_before_copy.subtree_equals(tree_after))):
        tree_before_copy.dump_json("debugging1.json")
        tree_after.dump_json("debugging2.json")
        return None

    return added, deleted, moved

def annotate_with_diff(mutable_tree_1, mutable_tree_2):
    added, deleted, moved = get_chawathe_edit_script(mutable_tree_1, mutable_tree_2)

    for m in added:
        m['attributes']['diff'] = "added"

    for m in deleted:
        m['attributes']['diff'] = "deleted"
    for m1, m2 in moved:
        m1['attributes']['diff'] = "moved"
        m2['attributes']['diff'] = "moved"
