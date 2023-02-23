from parsing.ast import ASTNode
from parsing.parser import *
import json
from analyzers.gumtree import gumtree

if __name__ == "__main__":
    with open("Vacuum348/GOOD_348_C4C30_session_data_last_program.json") as f:
        program_good = json.load(f)
    tree_good = build_ast_tree(program_good["targets"][0]["blocks"])
    with open("Vacuum348/BAD_348_C4C32_session_data.json") as f:
        program_bad = json.load(f)
    tree_bad = build_ast_tree(program_bad[0]["frames"][-2]["state_info"]["program"]["targets"][0]["blocks"])
    # with open("temp_code.json", "w") as f:
    #     json.dump(tree_good, f, indent=3)
    gumtree(tree_good, tree_bad)
    pass