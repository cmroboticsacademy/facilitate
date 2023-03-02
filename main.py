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
        json.dump(tree_good, f, indent=3, default=lambda x: x.name)
    
    def print_parents(astnode):
        print(astnode.parent)
    
    # tree_good.accept(print_parents)
    
    mappings = gumtree(tree_good, tree_bad)
    for m in mappings:
        print(m)
    pass