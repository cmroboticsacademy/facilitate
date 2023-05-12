
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

# Getting the diff

There are two methods for getting the diff: `get_edit_script` and `get_chawathe_edit_script`, both in  `analyzers/gumtree.py`.
Both these methods will call gumtree and return a lists of nodes that were added, deleted, and moved.

Weighting the nodes should be a matter of going through the lists and counting how many nodes of each type are present.

`get_chawathe_edit_script` is probably more recommended since it's based on the algorithm other research papers used. But that depends if I can get the bugs out in time.

# Visualizing

The `ASTNode` class has a `dump_json` function that takes a filename and dumps a JSON that is readable by the tree visualization program.

FYI -- because of this, the `.gitignore` automatically ignores JSON files, so if you add more testing JSONs, you will have to manually add them.

If you want to visualize a tree that's been annotated with nodes that are added, removed or moved, the `gumtree.py` file contains a method called `annotate_with_diff` that takes two trees, calls `get_chawathe_edit_script`, and modifies the trees in the parameter to show whether the node has been added, removed, or moved when the tree is dumped to a json.

# Importing CS2N data

To parse and organzie CS2N data, download the data files for the two databases (`play_sessions` and `sessions_data`) as CSVs, make sure the main block at the bottom of `student_program_util.py` points to those CSVs, and call `python3 student_program_util.py`.

That will generate a data structure (indicated in `diagram.png`) of all the sessions, organized by user ID, then challenge name, then sessions and episodes. This data structure is saved in `organized_sessions.pkl` for quick loading. To load the data structure in your program, call:

```
with open("organized_sessions.pkl", 'rb') as f:
    organized_sessions = pickle.load(f)
```

**Note on versions:** I parse the rows of the database based on their data gathering version (since pre-1.0.4 and post 1.0.5 have different parsing methods). You may need to include or exclude certain versions of data or put other filtering mechanisms in the `pickle_db_csv` function.

# Using the CS2N data

Once you've generated the pickle file, you can load the data structure in and query it using the `find_session` function in `student_program_util.py`. This function takes the user id, challenge name, and data structure of sessions, and returns the latest (most recent) session for that user/challenge name. 

For example, for user "1000" and challenge "cleaning_the_home" call `find_session(1000, "cleaning_the_home", organized session)` for the list of episodes. Each episode includes all the episode frames, programming interface frames leading up to the episode, the program being executed, and whether that episode passed or failed.

You can directly access the data structure as well, by iterating through the user ids or the sessions for a given user.
For example, if you want all the challenge names that a user has worked on, this would be a bit more complicated, since the challenge names are stored at the episode level. I would write:

```
challenges = set()
for session in organized_sessions[user_id]:
    if len(session) > 0:
        challenges.add(session[0].challenge_name)
```

Feel free to extend `student_program_util.py` with other functions for interfacing with the sessions data structure.

# Known problems, details, and potential improvements

The edit script algorithms may have extra "move" actions for adding and removing nodes in the middle of the tree. That's because the node following the added/removed node is technically "moved" as in their parent has changed. There shouldn't be too many, though, since this only affects the immediate children of the added/removed node.

For some reason, one of the tests for moving nodes is causing a circular tree. Still debugging this.

There are three ways of checking node equality: the `==` operator, which checks only blockid and is useful for tracking whether the same node is being referenced, `node_equals` which checks whether the operators, inputs, and fields are the same, and `subtree_equals`, which checks if a node and all their children are the same.

There is potential to streamline the way fields and inputs are represented. Right now, they contain lots of repetetive nodes, but we can imagine a node with a particular value (In fact, the Chawathe edit script algorithm accounts for such an `update` action, but I haven't implemented it). 