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
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
import sys
from student_program_util import Episode

with open("organized_sessions.pkl", 'rb') as f:
    organized_sessions = pickle.load(f)

def find_session(userid:int, challengename:str) -> list:
    for session in reversed(organized_sessions[userid]):
        if len(session) > 0 and session[0].challenge_name == challengename:
            return session
    return []

all_activities = set()
for uid, session_list in organized_sessions.items():
    for s in session_list:
        all_activities.add(s[0].challenge_name)

all_activities = list(all_activities)


def cluster_passing(challenge_name):
    print()
    print("**********************************************************")
    print(challenge_name)

    passing_progs = []
    for uid in organized_sessions.keys():
        session = find_session(uid, challenge_name)
        for episode in session:
            if episode.passing:
                passing_progs.append(episode)
    if len(passing_progs) <= 1:
        print("not enough passing programs")
        return
    distance_matrix = np.zeros((len(passing_progs), len(passing_progs)))
    for i in range(1, len(passing_progs)):
        for j in range(1, len(passing_progs)):
            if i == j:
                continue
            prev_program = json.loads(passing_progs[i].program)['targets'][0]['blocks']
            curr_program = json.loads(passing_progs[j].program)['targets'][0]['blocks']
            prev_tree = build_ast_tree(prev_program)
            new_tree = build_ast_tree(curr_program)
            added, deleted, moved = get_edit_script(prev_tree, new_tree)
            score = len(added) + len(deleted) + len(moved)
            distance_matrix[i][j] = (score)

    np.set_printoptions(threshold=sys.maxsize)
    print(distance_matrix)
            
            
    db_cluster = DBSCAN(eps=25, min_samples=3, 
        metric='precomputed').fit(distance_matrix)

    print(db_cluster.labels_)
    # print(db_cluster.core_sample_indices_)

    ac_cluster = AgglomerativeClustering(n_clusters= None, affinity="precomputed", 
        compute_full_tree='True', linkage="average", distance_threshold=40).fit(distance_matrix)
    print(ac_cluster.n_clusters_)
    print(ac_cluster.labels_)
    # find "center" of each agglomerative cluster
    all_clusters = [[] for _ in range(ac_cluster.n_clusters_)]
    for i, l in enumerate(ac_cluster.labels_):
        all_clusters[l].append(i)
    cluster_centers = []
    for c in all_clusters:
        distances = [sum([distance_matrix[i][j] for j in c]) for i in c]
        min_pos = distances.index(min(distances))
        cluster_centers.append(c[min_pos])
    print(cluster_centers)
    if challenge_name == "spike_curric_exploring_a_disaster_site_challenge":
        for c_idx, c in enumerate(cluster_centers):
            with open(f"cluster{c_idx}.json", "w") as f:
                center_tree = build_ast_tree(json.loads(passing_progs[c].program)['targets'][0]['blocks'])
                json.dump(center_tree, f, indent=3, default=lambda x: x.name)


for a in all_activities:
    if a == "spike_curric_getting_started_curriculum": # don't know what's up with this one
        continue
    if "challenge" in a:
        cluster_passing(a)

