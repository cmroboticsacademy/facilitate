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
# main
if __name__ == "__main__":
    with open("Vacuum348/GOOD_348_C4C30_session_data_last_program.json") as f:
        program_good = json.load(f)
    tree_good = build_ast_tree(program_good["targets"][0]["blocks"])
    with open("Vacuum348/BAD_348_C4C32_session_data.json") as f:
        program_bad = json.load(f)
    tree_bad = build_ast_tree(program_bad[0]["frames"][-2]["state_info"]["program"]["targets"][0]["blocks"])
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
    
    mappings = gumtree(tree_bad, tree_good)
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
    tree_bad.accept_no_children(get_del_nodes)

    added = []
    def get_add_nodes(after_node):
        if after_node not in afters:
            added.append(after_node)
            for c in after_node.children:
                c.accept_no_children(get_add_nodes)
    tree_good.accept_no_children(get_add_nodes)

    # for m in mappings:
    #     print(m)

    print(len(deleted), " nodes deleted")
    print(len(added), " nodes added")
    pass