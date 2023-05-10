from parsing.ast import ASTNode
from parsing.parser import *
import json
from analyzers.gumtree import get_edit_script, annotate_with_diff
from analyzers.statementlistvisitor import NodeListVisitor
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from io import StringIO
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans, DBSCAN
from student_program_util import Episode




with open("organized_sessions.pkl", 'rb') as f:
    organized_sessions = pickle.load(f)

def find_session(userid:int, challengename:str) -> list:
    for session in reversed(organized_sessions[userid]):
        if len(session) > 0 and session[0].challenge_name == challengename:
            return session
    return []

all_uids = list(organized_sessions.keys())


# Pick out some interesting cases

sesh = find_session(1927379, "spike_curric_cleaning_the_home_myblocks_challenge")


sesh_correct = find_session(1947084, "spike_curric_cleaning_the_home_myblocks_challenge")
for ep in sesh_correct:
    if ep.passing:
        print(ep.program)
        correct_program = build_ast_tree(json.loads(ep.program)['targets'][0]['blocks'])

prev_program = json.loads(sesh[1].program)['targets'][0]['blocks']
added, deleted, moved = get_edit_script(build_ast_tree(prev_program), correct_program)

trajectory = [len(added) + len(deleted) + len(moved)]

for i in range(2, len(sesh)-1):
    curr_program = json.loads(sesh[i].program)['targets'][0]['blocks']
    prev_tree = build_ast_tree(prev_program)
    new_tree = build_ast_tree(curr_program)

    with open("studenttree1.json", "w") as f:
        json.dump(prev_tree, f, indent=3, default=lambda x: x.name)

    with open("studenttree2.json", "w") as f:
        json.dump(new_tree, f, indent=3, default=lambda x: x.name)

    added, deleted, moved = get_edit_script(prev_tree, new_tree)
    print("added", len(added))
    print("deleted", len(deleted))
    print("moved", len(moved))

    added, deleted, moved = get_edit_script(new_tree, correct_program)
    trajectory.append(len(added) + len(deleted) + len(moved))
    
    prev_program = curr_program

print(trajectory)
# how similar are passing programs of one activity?

print("----- similarity ------")
"spike_curric_sequential_movements_mini_challenge_curriculum"
"spike_curric_90_degree_turn_try_it"
passing_progs = []
for uid in organized_sessions.keys():
    session = find_session(uid, "spike_curric_sequential_movements_mini_challenge_curriculum")
    for episode in session:
        if episode.passing:
            passing_progs.append(episode)
prev_program = json.loads(passing_progs[0].program)['targets'][0]['blocks']

for i in range(1, len(passing_progs)):
    curr_program = json.loads(passing_progs[i].program)['targets'][0]['blocks']
    prev_tree = build_ast_tree(prev_program)
    new_tree = build_ast_tree(curr_program)

    added, deleted, moved = get_edit_script(prev_tree, new_tree)
    print("added", len(added))
    print("deleted", len(deleted))
    print("moved", len(moved))
    if len(added) + len(deleted) + len(moved) > 0:
        with open("studenttree1.json", "w") as f:
            json.dump(prev_tree, f, indent=3, default=lambda x: x.name)

        with open("studenttree2.json", "w") as f:
            json.dump(new_tree, f, indent=3, default=lambda x: x.name)

    prev_program = curr_program

similarity_df = pd.DataFrame()
for episode in passing_progs:
    tree = build_ast_tree(json.loads(episode.program)['targets'][0]['blocks'])
    node_visitor = NodeListVisitor()
    tree.accept(node_visitor.visit)
    freq_series = pd.Series([str(n.op) for n in node_visitor.statement_list]).value_counts()
    freq_series = freq_series.rename_axis('unique_values').to_frame('counts')
    similarity_df = pd.concat([similarity_df, freq_series], axis=1)

similarity_df = similarity_df.fillna(0)
num_clusters = 4
km = KMeans(n_clusters=num_clusters).fit(similarity_df.T)

centers = pd.DataFrame(data = km.cluster_centers_, 
                  index = list(range(num_clusters)), 
                  columns = similarity_df.index)
center_strs = []
for r in centers.iterrows():
    program_elements = ""
    for k, v in r[1].iteritems():
        if v > 0:
            v = round(v)
            program_elements += ((str(k) + "\n") * v)
    center_strs.append(program_elements)

for i in range(len(center_strs)):
    print("cluster", i)
    print(center_strs[i])
    print()


# dbscan
distance_matrix = np.zeros((len(passing_progs), len(passing_progs)))
for i in range(len(passing_progs)):
    for j in range(len(passing_progs)):
        print(i, j)
        if i == j:
            continue
        prev_program = json.loads(passing_progs[i].program)['targets'][0]['blocks']
        curr_program = json.loads(passing_progs[j].program)['targets'][0]['blocks']
        prev_tree = build_ast_tree(prev_program)
        new_tree = build_ast_tree(curr_program)
        added, deleted, moved = get_edit_script(prev_tree, new_tree)
        score = len(moved)
        for n in added + deleted:
            if str(n.op).startswith("OpCodes.spike_movement"):
                score += 100
            else:
                score += 1
        distance_matrix[i][j] = score

print(distance_matrix)
        
        
db_cluster = DBSCAN(eps=150, min_samples=3, 
    metric='precomputed').fit(distance_matrix)

print(db_cluster.labels_)
print(db_cluster.core_sample_indices_)

# diff matrix - distance in clustering is the weighted diff between them


# print trajectory
# sesh = find_session(1947120, "spike_curric_turn_around_craters_mini_challenge")


# for ep in sesh:
#     if ep.passing:
#         print(ep.program)
#         correct_program = build_ast_tree(json.loads(ep.program)['targets'][0]['blocks'])
#         break

# prev_program = json.loads(sesh[1].program)['targets'][0]['blocks']
# added, deleted, moved = get_edit_script(build_ast_tree(prev_program), correct_program)

# trajectory = [len(added) + len(deleted) + len(moved)]

# for i in range(2, len(sesh)-1):
#     curr_program = json.loads(sesh[i].program)['targets'][0]['blocks']
#     prev_tree = build_ast_tree(prev_program)
#     new_tree = build_ast_tree(curr_program)

#     with open("studenttree1.json", "w") as f:
#         json.dump(prev_tree, f, indent=3, default=lambda x: x.name)

#     with open("studenttree2.json", "w") as f:
#         json.dump(new_tree, f, indent=3, default=lambda x: x.name)

#     added, deleted, moved = get_edit_script(prev_tree, new_tree)
#     print("added", len(added))
#     print("deleted", len(deleted))
#     print("moved", len(moved))

#     added, deleted, moved = get_edit_script(new_tree, correct_program)
#     trajectory.append(len(added) + len(deleted) + len(moved))
    
#     prev_program = curr_program

# print(trajectory)
