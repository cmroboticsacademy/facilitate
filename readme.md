
# Environment
All the tree code should work on a clean Python 3 install (I'm using 3.10.6).

Clustering uses SciKitLearn (I'm using 1.0.2). Some of the analysis is visualized with MatPlotLib (I'm using 3.5.2) and Seaborn (I'm using 0.11.2)

# Running tests
```
python3 -m unittest
```

The above command will run all tests:

* contained in the `test/` directory
* filename starts with `test_`
* test classes extend `unittest.TestCase`
* test functions start with `test_`

You can also run individual test files with `python3 -m test.{test_module name}`

# Structure
Data structure and parsing are contained in the `parsing/` folder.

Some the Gumtree diff algorithm is in the `analyzers/` folder, as well as some useful visitors (like counting how many nodes are in a tree).

Note on Gumtree: there are two edit script algorithms. One is the one I made up (`get_edit_script`) and one is adapted from the most common edit script algorithm (`get_chawathe_edit_script`). Both are tested for.

Tests live in the `test/` folder.

The file `student_program_util.py` contains the data structure and parser for interfacing with CS2N data.

The data structure is in a class called `Episode`, and the `pickle_db_csv` function takes the csv, parses it into the data structure (indicated by `diagram.png`), and pickles it so it can be easily loaded for other programs.
I'm not going to push the csv and pickle file I used, but if you need the data I used, let me know.

Some data analysis on CS2N programs is in `student_sample_statistics.py`. Clustering code is mostly in `clustering.py`

# Visualizing

The `ASTNode` class has a `dump_json` function that takes a filename and dumps a JSON that is readable by the tree visualization program.

FYI -- because of this, the `.gitignore` automatically ignores JSON files, so if you add more testing JSONs, you will have to manually add them.

# Known problems, details, and potential improvements

The edit script algorithms may have extra "move" actions for adding and removing nodes in the middle of the tree. That's because the node following the added/removed node is technically "moved" as in their parent has changed. There shouldn't be too many, though, since this only affects the immediate children of the added/removed node.

For some reason, one of the tests for moving nodes is causing a circular tree. Still debugging this.

There are three ways of checking node equality: the `==` operator, which checks only blockid and is useful for tracking whether the same node is being referenced, `node_equals` which checks whether the operators, inputs, and fields are the same, and `subtree_equals`, which checks if a node and all their children are the same.

There is potential to streamline the way fields and inputs are represented. Right now, they contain lots of repetetive nodes, but we can imagine a node with a particular value (In fact, the Chawathe edit script algorithm accounts for such an `update` action, but I haven't implemented it). 