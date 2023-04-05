import unittest

from parsing.ast import ASTNode
from parsing.parser import *
import json
from analyzers.gumtree import get_edit_script, annotate_with_diff
from analyzers.count import CountVisitor


class TestGumtree(unittest.TestCase):
    def runTest(self):
        self.tree1_tree2()
        self.tree2_tree3()
        self.tree2_tree4()
        self.tree4_tree5()

    def tree1_tree2(self):
        with open("test1.json") as f:
            program_1 = json.load(f)
        tree_1 = build_ast_tree(program_1["targets"][0]["blocks"])
        counter = CountVisitor()
        tree_1.accept(counter.visit)
        self.assertEqual(counter.counter, 6, "incorrect parsing")

        with open("test2.json") as f:
            program_2 = json.load(f)
        tree_2 = build_ast_tree(program_2["targets"][0]["blocks"])
        counter = CountVisitor()
        tree_2.accept(counter.visit)
        self.assertEqual(counter.counter, 11, "incorrect parsing")

        added, deleted, moved = get_edit_script(tree_1, tree_2)
        self.assertEqual(len(deleted), 0, "incorrect number of nodes deleted")
        self.assertEqual(len(added), 5, "incorrect number of nodes added")
        self.assertEqual(len(moved), 0, "incorrect number of nodes moved")



    def tree2_tree3(self):
        with open("test2.json") as f:
            program_2 = json.load(f)
        tree_2 = build_ast_tree(program_2["targets"][0]["blocks"])
        counter = CountVisitor()
        tree_2.accept(counter.visit)
        self.assertEqual(counter.counter, 11, "incorrect parsing")

        with open("test3.json") as f:
            program_3 = json.load(f)
        tree_3 = build_ast_tree(program_3["targets"][0]["blocks"])
        counter = CountVisitor()
        tree_3.accept(counter.visit)
        self.assertEqual(counter.counter, 14, "incorrect parsing")

        added, deleted, moved = get_edit_script(tree_2, tree_3)
        self.assertEqual(len(deleted), 0, "incorrect number of nodes deleted")
        self.assertEqual(len(added), 3, "incorrect number of nodes added")
        self.assertEqual(len(moved), 0, "incorrect number of nodes moved")

    def tree2_tree4(self):
        with open("test2.json") as f:
            program_2 = json.load(f)
        tree_2 = build_ast_tree(program_2["targets"][0]["blocks"])
        counter = CountVisitor()
        tree_2.accept(counter.visit)
        self.assertEqual(counter.counter, 11, "incorrect parsing")

        with open("test4.json") as f:
            program_4 = json.load(f)
        tree_4 = build_ast_tree(program_4["targets"][0]["blocks"])
        counter = CountVisitor()
        tree_4.accept(counter.visit)
        self.assertEqual(counter.counter, 20, "incorrect parsing")

        added, deleted, moved = get_edit_script(tree_2, tree_4)
        self.assertEqual(len(deleted), 0, "incorrect number of nodes deleted")
        self.assertEqual(len(added), 9, "incorrect number of nodes added")
        self.assertEqual(len(moved), 0, "incorrect number of nodes moved")

        annotate_with_diff(tree_2, tree_4)
        with open("annotated_tree1.json", 'w') as f:
            json.dump(tree_2, f, default=lambda x: x.name)
        with open("annotated_tree2.json", 'w') as f:
            json.dump(tree_4, f, default=lambda x: x.name)

    def tree4_tree5(self):
        with open("test4.json") as f:
            program_4 = json.load(f)
        tree_4 = build_ast_tree(program_4["targets"][0]["blocks"])
        counter = CountVisitor()
        tree_4.accept(counter.visit)
        self.assertEqual(counter.counter, 20, "incorrect parsing")

        with open("test5.json") as f:
            program_5 = json.load(f)
        tree_5 = build_ast_tree(program_5["targets"][0]["blocks"])
        counter = CountVisitor()
        tree_5.accept(counter.visit)
        self.assertEqual(counter.counter, 20, "incorrect parsing")

        added, deleted, moved = get_edit_script(tree_4, tree_5)
        self.assertEqual(len(deleted), 0, "incorrect number of nodes deleted")
        print(added)
        self.assertEqual(len(added), 0, "incorrect number of nodes added")
        self.assertEqual(len(moved), 1, "incorrect number of nodes moved")
unittest.main()