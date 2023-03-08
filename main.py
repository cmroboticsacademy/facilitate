from parsing.ast import ASTNode
from parsing.parser import *
import json
from analyzers.gumtree import gumtree
import cProfile


# timeout for profiling
import signal
from contextlib import contextmanager


@contextmanager
def timeout(time):
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time)

    try:
        yield
    except TimeoutError:
        pass
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


def raise_timeout(signum, frame):
    raise TimeoutError

def gumtree_timeout(time, tree_good, tree_bad):
    with timeout(time): 
        gumtree(tree_good, tree_bad)


def print_node_changes(tree_before, tree_after):
    mappings = gumtree(tree_before, tree_after)
    print(len(mappings), " subtree mappings found")
    # with open("temp_code.json", "w") as f:
    #     json.dump(mappings[0][0], f, indent=3, default=lambda x: x.name)
    # with open("tempcode_2.json", "w") as f:
    #     json.dump(mappings[0][1], f, indent=3, default=lambda x: x.name)

    befores, afters = zip(*mappings)

    deleted = []
    def get_del_nodes(before_node):
        if before_node not in befores:
            deleted.append(before_node)
            for c in before_node.children:
                c.accept_no_children(get_del_nodes)
    tree_before.accept_no_children(get_del_nodes)

    added = []
    def get_add_nodes(after_node):
        if after_node not in afters:
            added.append(after_node)
            for c in after_node.children:
                c.accept_no_children(get_add_nodes)
    tree_after.accept_no_children(get_add_nodes)

    moved = []
    i = 0
    while i < len(deleted):
        delnode = deleted[i]
        matching_index = -1
        for j in range(len(added)):
            if added[j].node_equals(delnode):
                matching_index = j
                break
        if matching_index >= 0:
            moved.append((delnode, added[matching_index]))
            del deleted[i]
            del added[matching_index]
        else:
            i += 1

    print(len(deleted), " nodes deleted")
    print(len(added), " nodes added")
    print(len(moved), " nodes moved")

# main
if __name__ == "__main__":
    with open("Vacuum348/GOOD_348_C4C30_session_data_last_program.json") as f:
        program_good = json.load(f)
    tree_good = build_ast_tree(program_good["targets"][0]["blocks"])
    with open("Vacuum348/BAD_348_C4C32_session_data.json") as f:
        program_bad = json.load(f)
    tree_bad = build_ast_tree(program_bad[0]["frames"][-2]["state_info"]["program"]["targets"][0]["blocks"])
    with open("Vacuum348/UGLY_348_C4C34_session_data.json") as f:
        program_ugly = json.load(f)
    tree_ugly = build_ast_tree(program_ugly[0]["frames"][-2]["state_info"]["program"]["targets"][0]["blocks"])
    with open("temp_code.json", "w") as f:
        json.dump(tree_bad, f, indent=3, default=lambda x: x.name)
    
    def print_parents(astnode):
        print(astnode.parent)

    count = 0
    def count_nodes(astnode):
        global count
        count+=1
    tree_good.accept(count_nodes)
    print(count, " nodes in good example")
    tree_bad.accept(count_nodes)
    print(count, " nodes in both the good and bad examples")

    print("----")
    print("before: bad, after: good")
    print_node_changes(tree_bad, tree_good)
    
    print("----")
    print("before: bad, after: ugly")
    print_node_changes(tree_bad, tree_ugly)

    print("----")
    print("before: ugly, after: good")
    print_node_changes(tree_ugly, tree_good)
    
    print("----")
    print("before: good, after: good")
    print_node_changes(tree_good, tree_good)