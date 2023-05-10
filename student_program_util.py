from parsing.ast import ASTNode
from parsing.parser import *
import json
import pandas as pd
from collections import defaultdict, Counter
from io import StringIO
import pickle


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

# TODO: change method based on version
def pickle_db_csv(play_sessions, session_data):
    play_sessions = pd.read_csv(play_sessions)
    play_sessions = play_sessions[play_sessions.user_id.notnull()]
    print(pd.unique(play_sessions.user_id))
    print(len(pd.unique(play_sessions.user_id)))
    play_sessions_versions = play_sessions.groupby("version", group_keys=False)

    session_data = pd.read_csv(session_data)
    session_data = session_data.set_index("_id")


    def parse_play_sessions_frames_1_0_4(row:int) -> pd.DataFrame:
        frames = play_sessions.frames[row]
        obj = json.loads(frames)
        for i, o in enumerate(obj):
            obj[i] = json.loads(obj[i])
        session = pd.DataFrame(obj)
        return session

    def parse_play_sessions_frames_1_0_5(row:int) -> pd.DataFrame:
        session_id = play_sessions._id[row]
        frames = json.loads(session_data['frames'][session_id])
        frames = [json.loads(f) for f in frames]
        return pd.DataFrame(frames)

    organized_sessions = defaultdict(list)
    other_actors = pd.DataFrame()

    def parse_frames(user_id, all_frames):
        
        episode_list = []
        passing = False
        state = ""
        challenge_name = ""
        curr_prog_interface = ""
        prev_prog_interface = ""
        curr_episode_data = ""
        frame_header = all_frames.columns.to_series().to_frame(1).T.to_csv(index=False).partition("\n")[0]
        print(all_frames.head())
        print(all_frames.state_info)


        for i, frame in all_frames.iterrows():
            if frame.actor == "episode_data":
                if frame.object_name == "challenge_pass":
                    passing = True
                if frame.verb == "episode_started":
                    challenge_name = frame.object_name
                    episode_list.append(Episode(
                        passing=passing, 
                        pi=pd.DataFrame(StringIO(f'{frame_header}\n{prev_prog_interface}')), 
                        ed=pd.DataFrame(StringIO(f'{frame_header}\n{curr_episode_data}')), 
                        program_rep=state, challenge_name=challenge_name))
                    state = json.dumps(json.loads(frame.state_info["program"]), sort_keys=True)
                    passing = False
                    prev_prog_interface = curr_prog_interface
                    curr_prog_interface = ""
                    curr_episode_data = ""
                    
                curr_episode_data = f'{curr_episode_data}{frame.to_frame(1).T.to_csv(header=False, index=False)}'
            elif frame.actor == "programming_interface":
                curr_prog_interface = f'{curr_prog_interface}{frame.to_frame(1).T.to_csv(header=False, index=False)}'
            else:
                # why is there no concat in place T_T
                temp = pd.concat([other_actors, frame.to_frame(1).T],  ignore_index=True, sort=True)
                other_actors.drop(other_actors.index[0:], inplace=True)
                other_actors[temp.columns] = temp 

        # record last episode and last program changes
        episode_list.append(Episode(
            passing=passing, 
            pi=pd.DataFrame(StringIO(prev_prog_interface)), 
            ed=pd.DataFrame(StringIO(curr_episode_data)), 
            program_rep=state, challenge_name=challenge_name))
        if len(curr_prog_interface) > 0:
            episode_list.append(Episode(
                passing=False, 
                pi=pd.DataFrame(StringIO(curr_prog_interface)), 
                ed=pd.DataFrame(columns=all_frames.columns), 
                program_rep="", challenge_name=challenge_name))
            
        organized_sessions[user_id].append(episode_list)
        organized_sessions[0].append([])

    # for i, all_frames in iter_enum_session_frames():
    def parse_1_0_4(row):
        user_id = play_sessions.user_id[row.name]
        all_frames = parse_play_sessions_frames_1_0_4(row.name)
        parse_frames(user_id, all_frames)

    def parse_1_0_5(row):
        user_id = play_sessions.user_id[row.name]
        all_frames = parse_play_sessions_frames_1_0_5(row.name)
        parse_frames(user_id, all_frames)
    
    # play_sessions_versions.get_group("1.0.3").apply(parse_1_0_4, axis=1)
    # play_sessions_versions.get_group("1.0.4").apply(parse_1_0_4, axis=1)
    play_sessions_versions.get_group("1.0.5").apply(parse_1_0_5, axis=1)



    with open("organized_sessions.pkl", 'wb') as f:
        pickle.dump(organized_sessions, f)

    print("pickled")

pickle_db_csv("initial-analysis/play_sessions.csv", "session_data.csv")
