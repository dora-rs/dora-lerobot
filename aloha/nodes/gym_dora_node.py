import gymnasium as gym

import gym_dora  # noqa: F401
import pandas as pd
import time
from pathlib import Path

env = gym.make(
    "gym_dora/DoraAloha-v0", disable_env_checker=True, max_episode_steps=5000
)
observation = env.reset()


class ReplayPolicy:
    def __init__(self, example_path, epidode=1):
        df_action = pd.read_parquet(example_path / "action.parquet")
        df_episode_index = pd.read_parquet(example_path / "episode_index.parquet")
        self.df = pd.merge_asof(
            df_action[["timestamp_utc", "action"]],
            df_episode_index[["timestamp_utc", "episode_index"]],
            on="timestamp_utc",
            direction="backward",
        )
        # self.df["episode_index"] = self.df["episode_index"].map(lambda x: x[0])
        self.df = self.df[self.df["episode_index"] == epidode]
        self.current_time = self.df["timestamp_utc"].iloc[0]
        self.topic = "action"
        self.index = 0
        self.finished = False

    def select_action(self, obs):
        if self.index < len(self.df):
            self.index += 1
        else:
            self.finished = True
        row = self.df.iloc[self.index]
        delta_time = (row["timestamp_utc"] - self.current_time).microseconds
        self.current_time = row["timestamp_utc"]
        if delta_time > 0:
            time.sleep(delta_time / 1_000_000)
        return row[self.topic], self.finished


policy = ReplayPolicy(
    Path(
        "/home/rcadene/dora-aloha/aloha/graphs/out/018f9b3d-d821-7ea5-9cf0-f6ea8aa7f8f9"
    )
)
done = False
while not done:
    actions, finished = policy.select_action(observation)

    observation, reward, terminated, truncated, info = env.step(actions)
    if terminated:
        print(observation, reward, terminated, truncated, info, flush=True)
    done = terminated | truncated | done | finished

env.close()
