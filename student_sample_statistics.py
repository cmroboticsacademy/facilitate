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



class Episode():
    def __init__(self):
        self.passing = False
        self.programming_interface = pd.DataFrame()
        self.episode_data = pd.DataFrame()
        self.program = ""
        self.challenge_name = ""

    def __init__(self, pi:pd.DataFrame, ed:pd.DataFrame, passing:bool, program_rep:str, challenge_name:str):
        self.passing = passing
        self.programming_interface = pi
        self.episode_data = ed
        self.program = program_rep
        self.challenge_name = challenge_name
    def __str__(self):
        return str(self.episode_data)



# parsing raw data, can remove after saving organized_sessions
# raw_data = pd.read_csv("initial-analysis/play_sessions.csv")
# raw_data = raw_data[raw_data.user_id.notnull()]
# print(pd.unique(raw_data.user_id))
# print(len(pd.unique(raw_data.user_id)))
# import sys
# sys.exit("Error message")
# raw_data = raw_data[raw_data.version == "1.0.3"]
# raw_data = raw_data.reset_index()

# def parse_raw_data_frames(row:int) -> pd.DataFrame:
#     frames = raw_data.frames[row]
#     obj = json.loads(frames)
#     for i, o in enumerate(obj):
#         obj[i] = json.loads(obj[i])
#     session = pd.DataFrame(obj)
#     return session

# memo_frames = {}

# def iter_session_frames():
#     for i in raw_data.index:
#         if i not in memo_frames:   
#             frames = parse_raw_data_frames(i)
#             memo_frames[i] = frames
#         yield memo_frames[i].copy()

# def iter_enum_session_frames(): #TODO: uh make this not a weird copy
#     for i in raw_data.index:
#         yield i, parse_raw_data_frames(i)


# organized_sessions = defaultdict(list)
# other_actors = pd.DataFrame()

# for i, all_frames in iter_enum_session_frames():
#     if len(all_frames) == 0:
#         continue
#     user_id = raw_data.user_id[i]
    
#     episode_list = []
#     passing = False
#     state = ""
#     challenge_name = ""
#     curr_prog_interface = ""
#     prev_prog_interface = ""
#     curr_episode_data = ""
#     frame_header = all_frames.columns.to_series().to_frame(1).T.to_csv(index=False).partition("\n")[0]

#     for i, frame in all_frames.iterrows():
#         if frame.actor == "episode_data":
#             if frame.object_name == "challenge_pass":
#                 passing = True
#             if frame.verb == "episode_started":
#                 challenge_name = frame.object_name
#                 episode_list.append(Episode(
#                     passing=passing, 
#                     pi=pd.DataFrame(StringIO(f'{frame_header}\n{prev_prog_interface}')), 
#                     ed=pd.DataFrame(StringIO(f'{frame_header}\n{curr_episode_data}')), 
#                     program_rep=state, challenge_name=challenge_name))
#                 state = json.dumps(json.loads(frame.state_info["program"]), sort_keys=True)
#                 passing = False
#                 prev_prog_interface = curr_prog_interface
#                 curr_prog_interface = ""
#                 curr_episode_data = ""
                
#             curr_episode_data = f'{curr_episode_data}{frame.to_frame(1).T.to_csv(header=False, index=False)}'
#         elif frame.actor == "programming_interface":
#             curr_prog_interface = f'{curr_prog_interface}{frame.to_frame(1).T.to_csv(header=False, index=False)}'
#         else:
#             other_actors = pd.concat([other_actors, frame.to_frame(1).T],  ignore_index=True, sort=True)
#     # record last episode and last program changes
#     episode_list.append(Episode(
#         passing=passing, 
#         pi=pd.DataFrame(StringIO(prev_prog_interface)), 
#         ed=pd.DataFrame(StringIO(curr_episode_data)), 
#         program_rep=state, challenge_name=challenge_name))
#     if len(curr_prog_interface) > 0:
#         episode_list.append(Episode(
#             passing=False, 
#             pi=pd.DataFrame(StringIO(curr_prog_interface)), 
#             ed=pd.DataFrame(columns=all_frames.columns), 
#             program_rep="", challenge_name=challenge_name))
        
#     organized_sessions[user_id].append(episode_list)
# with open("organized_sessions.pkl", 'wb') as f:
#     pickle.dump(organized_sessions, f)

# print("pickled")
# end parsing

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
