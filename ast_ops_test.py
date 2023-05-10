import unittest

from parsing.ast import ASTNode
from parsing.parser import *
import json
from analyzers.gumtree import get_edit_script, annotate_with_diff, get_chawathe_edit_script
from analyzers.count import CountVisitor


class TestASTOps(unittest.TestCase):
    def runTest(self):
        self.test_add_child()
        self.test_remove_child()

    def test_add_child(self):
        with open("test1.json") as f:
            program_1 = json.load(f)
        tree_1 = build_ast_tree(program_1["targets"][0]["blocks"])
        counter = CountVisitor()
        tree_1.accept(counter.visit)
        self.assertEqual(counter.counter, 6, "incorrect parsing")

        self.assertEqual(len(tree_1.children), 1, "incorrect parsing of children")
        self.assertEqual(len(tree_1.next), 1, "incorrect parsing of children")
        self.assertEqual(len(tree_1.inputs), 0, "incorrect parsing of children")
        self.assertEqual(len(tree_1.fields), 0, "incorrect parsing of children")

        nextnode = ASTNode(parent=tree_1, blockid="testnext", desc="noop")
        tree_1.add_child(nextnode)

        self.assertEqual(len(tree_1.children), 2, "incorrect adding next")
        self.assertEqual(len(tree_1.next), 2, "incorrect adding next")
        self.assertEqual(len(tree_1.inputs), 0, "incorrect adding next")
        self.assertEqual(len(tree_1.fields), 0, "incorrect adding next")
        self.assertEqual(nextnode.parent, tree_1, "child node parent not properly added")

        fieldnode = ASTNode(parent=tree_1, blockid="testfield", desc="noop")
        tree_1.add_child(fieldnode, childtype="fields")

        self.assertEqual(len(tree_1.children), 3, "incorrect adding field")
        self.assertEqual(len(tree_1.next), 2, "incorrect adding field")
        self.assertEqual(len(tree_1.inputs), 0, "incorrect adding field")
        self.assertEqual(len(tree_1.fields), 1, "incorrect adding field")
        self.assertEqual(fieldnode.parent, tree_1, "child node parent not properly added")

        inputnode = ASTNode(parent=tree_1, blockid="testinput", desc="noop")
        tree_1.add_child(inputnode, childtype="inputs")

        self.assertEqual(len(tree_1.children), 4, "incorrect adding input")
        self.assertEqual(len(tree_1.next), 2, "incorrect adding input")
        self.assertEqual(len(tree_1.inputs), 1, "incorrect adding input")
        self.assertEqual(len(tree_1.fields), 1, "incorrect adding input")
        self.assertEqual(nextnode.parent, tree_1, "child node parent not properly added")

        # with open("test2.json") as f:
        #     program_2 = json.load(f)
        # tree_2 = build_ast_tree(program_2["targets"][0]["blocks"])
        # counter = CountVisitor()
        # tree_2.accept(counter.visit)
        # self.assertEqual(counter.counter, 11, "incorrect parsing")

    def test_remove_child(self):
        with open("test1.json") as f:
            program_1 = json.load(f)
        tree_1 = build_ast_tree(program_1["targets"][0]["blocks"])
        counter = CountVisitor()
        tree_1.accept(counter.visit)
        self.assertEqual(counter.counter, 6, "incorrect parsing")

        self.assertEqual(len(tree_1.children), 1, "incorrect parsing of children")
        self.assertEqual(len(tree_1.next), 1, "incorrect parsing of children")
        self.assertEqual(len(tree_1.inputs), 0, "incorrect parsing of children")
        self.assertEqual(len(tree_1.fields), 0, "incorrect parsing of children")

        to_delete = tree_1.children[0]

        self.assertEqual(len(to_delete.children), 1, "incorrect parsing of children")
        self.assertEqual(len(to_delete.inputs), 1, "incorrect parsing of children")
        self.assertEqual(to_delete.parent, tree_1, "incorrect parsing of children")

        tree_1.remove_child(to_delete)

        self.assertEqual(len(tree_1.children), 0, "incorrect removal of children")
        self.assertEqual(len(tree_1.next), 0, "incorrect removal of children")
        self.assertEqual(len(tree_1.inputs), 0, "incorrect removal of children")
        self.assertEqual(len(tree_1.fields), 0, "incorrect removal of children")

        self.assertEqual(len(to_delete.children), 1, "incorrect removal of children")
        self.assertEqual(len(to_delete.inputs), 1, "incorrect removal of children")
        self.assertIsNone(to_delete.parent, "incorrect removal of children")

    def test_move_child(self):
        with open("test1.json") as f:
            program_1 = json.load(f)
        tree_1 = build_ast_tree(program_1["targets"][0]["blocks"])
        counter = CountVisitor()
        tree_1.accept(counter.visit)
        self.assertEqual(counter.counter, 6, "incorrect parsing")

        def ensure_1_or_0_children(node):
            self.assertIn(len(node.children), [0, 1], "incorrect parsing of children")
        
        tree_1.accept(ensure_1_or_0_children)

        next = tree_1.children[0] # spike_movement_direction
        next = next.children[0] # DIRECTION
        next = next.children[0] # spike_movement_direction_picker
        next = next.children[0] # SPIN_DIRECTIONS

        parent_from = next.parent
        parent_from.remove_child(next)
        self.assertIsNone(next.parent, "incorrect removal")
        self.has_n_children(parent_from, 0)
        self.has_n_children(next, 1)

        parent_to = tree_1.children[0].children[0]
        parent_to.add_child(next)
        self.assertEqual(next.parent, parent_to, "incorrect add")
        self.has_n_children(parent_to, 2)
        self.has_n_children(next, 1)

        def check_children_counts(node):
            if node == parent_to:
                self.has_n_children(node, 2)
            elif node == parent_from:
                self.has_n_children(node, 0)
            else:
                self.assertIn(len(node.children), [0,1], "incorrect move")

        tree_1.accept(check_children_counts)

    def has_n_children(self, node, n):
        self.assertEqual(len(node.children), n, "incorrect number of children")

    def test_move_children(self):
        with open("test4.json") as f:
            program_4 = json.load(f)
        tree_4 = build_ast_tree(program_4["targets"][0]["blocks"])
        counter = CountVisitor()
        tree_4.accept(counter.visit)
        self.assertEqual(counter.counter, 20, "incorrect parsing")

        self.has_n_children(tree_4, 1)
        c1 = tree_4.children[0] # spike_movement_direction_for_duration
        self.has_n_children(c1, 4)
        c2 = c1.next[0] # spike_movement_direction
        self.has_n_children(c2, 2)
        c3 = c2.next[0] # spike_movement_direction
        self.has_n_children(c3, 1)

        # moving c2 from c1 to the root
        c1.remove_child(c2)
        self.assertIsNone(c2.parent, "incorrect removal")
        self.has_n_children(c1, 3)
        self.has_n_children(c2, 2)

        tree_4.add_child(c2)
        self.assertEqual(c2.parent, tree_4, "incorrect add")
        self.has_n_children(tree_4, 2)
        self.has_n_children(c2, 2)

        # moving c3 from c2 to the c1
        c2.remove_child(c3)
        self.assertIsNone(c3.parent, "incorrect removal")
        self.has_n_children(c2, 1)
        self.has_n_children(c3, 1)

        c1.add_child(c3)
        self.assertEqual(c3.parent, c1, "incorrect add")
        self.has_n_children(c1, 4)
        self.has_n_children(c3, 1)


        def check_children_counts(node):
            if node == tree_4:
                self.has_n_children(node, 2)
            elif node == c1:
                self.has_n_children(node, 4)
            elif node == c2:
                self.has_n_children(node, 1)
            elif node == c3:
                self.has_n_children(node, 1)
            else:
                self.assertIn(len(node.children), [0,1], "incorrect move")

        tree_4.accept(check_children_counts)

    def test_equals1(self):
        node1 = ASTNode(None, "123", "Yes")
        node2 = ASTNode(None, "456", "Yes")
        self.assertTrue(node1.node_equals(node2))
        self.assertNotEqual(node1, node2)
        self.assertTrue(node1 != node2)

    def test_equals2(self):
        node1 = ASTNode(None, "123", "Yes")
        node2 = ASTNode(None, "123", "No")
        self.assertFalse(node1.node_equals(node2))
        self.assertEqual(node1, node2)
        self.assertTrue(node1 == node2)
        self.assertFalse(node1 != node2) # does not pass?????????
        self.assertFalse(not (node1 == node2))

    def test_equals3(self):
        node1 = ASTNode(None, "123", "Yes")
        parent = ASTNode(None, "parent", "parent_op")
        node2 = ASTNode(parent, "123", "Yes")
        self.assertTrue(node1.node_equals(node2))
        self.assertEqual(node1, node2)

    def test_equals4(self):
        node1 = ASTNode(None, "123", "Yes")
        node2 = ASTNode(None, "123", "No")
        self.assertFalse(node1.subtree_equals(node2))
        self.assertEqual(node1, node2)

    def test_equals5(self):
        node1 = ASTNode(None, "123", "Yes")
        node1_child = ASTNode(node1, "456", "child1")
        node1.add_child(node1_child)
        node2 = ASTNode(None, "123", "Yes")
        self.assertFalse(node1.subtree_equals(node2))
        self.assertTrue(node1.node_equals(node2))
        self.assertEqual(node1, node2)

    def test_equals6(self):
        node1 = ASTNode(None, "123", "Yes")
        node1_child = ASTNode(node1, "child1", "same_child_op")
        node1.add_child(node1_child)
        node2 = ASTNode(None, "456", "Yes")
        node2_child = ASTNode(node2, "child2", "same_child_op")
        node2.add_child(node2_child)
        self.assertTrue(node1.subtree_equals(node2))
        self.assertTrue(node1.node_equals(node2))
        self.assertNotEqual(node1, node2)

    def test_equals7(self):
        node1 = ASTNode(None, "123", "Yes")
        node1_child = ASTNode(node1, "child1", "child_op")
        node1.add_child(node1_child)
        node2 = ASTNode(None, "456", "Yes")
        node2_child = ASTNode(node2, "child2", "diff_child_op")
        node2.add_child(node2_child)
        self.assertFalse(node1.subtree_equals(node2))
        self.assertTrue(node1.node_equals(node2))
        self.assertNotEqual(node1, node2)

    def test_equals8(self):
        node1 = ASTNode(None, "123", "Yes")
        node1_input = ASTNode(node1, "input1", "input_op")
        node1.add_child(node1_input, "inputs")
        node2 = ASTNode(None, "123", "Yes")
        node2_input = ASTNode(node2, "input2", "diff_input_op")
        node2.add_child(node2_input, "inputs")
        self.assertFalse(node1.subtree_equals(node2))
        self.assertFalse(node1.node_equals(node2))
        self.assertNotEqual(node1, node2)

    def test_equals9(self):
        node1 = ASTNode(None, "123", "Yes")
        node1_input = ASTNode(node1, "input1", "input_op")
        node1_input_child = ASTNode(node1_input, "input_child", "child1")
        node1_input.add_child(node1_input_child)
        node1.add_child(node1_input, "inputs")
        node2 = ASTNode(None, "123", "Yes")
        node2_input = ASTNode(node2, "input2", "input_op")
        node2_input_child = ASTNode(node2_input, "input_child", "child2")
        node2_input.add_child(node2_input_child)
        node2.add_child(node2_input, "inputs")
        self.assertFalse(node1.subtree_equals(node2))
        self.assertFalse(node1.node_equals(node2))
        self.assertEqual(node1, node2)

    def test_equals9(self):
        node1 = ASTNode(None, "123", "Yes")
        node1_input = ASTNode(node1, "input1", "input_op")
        node1_input_child = ASTNode(node1_input, "input_child", "child_op")
        node1_input.add_child(node1_input_child)
        node1.add_child(node1_input, "inputs")
        node2 = ASTNode(None, "123", "Yes")
        node2_input = ASTNode(node2, "input2", "input_op")
        node2_input_child = ASTNode(node2_input, "input_child", "child_op")
        node2_input.add_child(node2_input_child)
        node2.add_child(node2_input, "inputs")
        self.assertTrue(node1.subtree_equals(node2))
        self.assertTrue(node1.node_equals(node2))
        self.assertEqual(node1, node2)

    def test_equals10(self):
        node1 = ASTNode(None, "123", "Yes")
        node1_input = ASTNode(node1, "input1", "input_op")
        node1_input_child = ASTNode(node1_input, "input_child", "child_op")
        node1_input.add_child(node1_input_child)
        node1.add_child(node1_input, "inputs")

        node1_next = ASTNode(node1, "456", "next_op")
        node1.add_child(node1_next)

        node2 = ASTNode(None, "123", "Yes")
        node2_input = ASTNode(node2, "input2", "input_op")
        node2_input_child = ASTNode(node2_input, "input_child", "child_op")
        node2_input.add_child(node2_input_child)
        node2.add_child(node2_input, "inputs")
        self.assertFalse(node1.subtree_equals(node2))
        self.assertTrue(node1.node_equals(node2))
        self.assertEqual(node1, node2)

unittest.main()