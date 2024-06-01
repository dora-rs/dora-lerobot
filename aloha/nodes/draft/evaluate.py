from config.config import (
    POLICY_CONFIG,
    TASK_CONFIG,
    TRAIN_CONFIG,
    ROBOT_PORTS,
)  # must import first

import os
import cv2
import torch
import pickle
import argparse
from time import time

from robot import Robot
from training.utils import *
import numpy as np

# parse the task name via command line
task = "sort6"

# config
cfg = TASK_CONFIG
policy_config = POLICY_CONFIG
train_cfg = TRAIN_CONFIG
device = os.environ["DEVICE"]


def capture_image(cam):
    # Capture a single frame
    _, frame = cam.read()
    # Generate a unique filename with the current date and time
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Define your crop coordinates (top left corner and bottom right corner)
    # x1, y1 = 400, 0  # Example starting coordinates (top left of the crop rectangle)
    # x2, y2 = 1600, 900  # Example ending coordinates (bottom right of the crop rectangle)
    # # Crop the image
    # image = image[y1:y2, x1:x2]
    # Resize the image
    image = cv2.resize(
        image, (cfg["cam_width"], cfg["cam_height"]), interpolation=cv2.INTER_AREA
    )

    return image


import gymnasium as gym

import gym_dora  # noqa: F401

env = gym.make(
    "gym_dora/DoraAloha-v0", disable_env_checker=True, max_episode_steps=10000
)

if __name__ == "__main__":
    # init camera
    # Check if the camera opened successfully
    # init follower

    # load the policy
    ckpt_path = os.path.join(
        train_cfg["checkpoint_dir"], task, train_cfg["eval_ckpt_name"]
    )
    policy = make_policy(policy_config["policy_class"], policy_config)
    loading_status = policy.load_state_dict(
        torch.load(ckpt_path, map_location=torch.device(device))
    )
    print(loading_status)
    policy.to(device)
    policy.eval()

    print(f"Loaded: {ckpt_path}")
    stats_path = os.path.join(train_cfg["checkpoint_dir"], task, f"dataset_stats.pkl")
    with open(stats_path, "rb") as f:
        stats = pickle.load(f)

    pre_process = lambda s_qpos: (s_qpos - stats["qpos_mean"]) / stats["qpos_std"]
    post_process = lambda a: a * stats["action_std"] + stats["action_mean"]

    query_frequency = policy_config["num_queries"]
    if policy_config["temporal_agg"]:
        query_frequency = 1
        num_queries = policy_config["num_queries"]

    obs = env.reset()

    os.system('spd-say "start"')

    n_rollouts = 1
    for i in range(n_rollouts):
        ### evaluation loop
        if policy_config["temporal_agg"]:
            all_time_actions = torch.zeros(
                [cfg["episode_len"], cfg["episode_len"] + num_queries, cfg["state_dim"]]
            ).to(device)
        qpos_history = torch.zeros((1, cfg["episode_len"], cfg["state_dim"])).to(device)
        with torch.inference_mode():
            # init buffers
            obs_replay = []
            action_replay = []
            for t in range(cfg["episode_len"]):
                qpos_numpy = np.array(obs["qpos"])
                qpos = pre_process(qpos_numpy)
                qpos = torch.from_numpy(qpos).float().to(device).unsqueeze(0)
                qpos_history[:, t] = qpos
                curr_image = get_image(obs["pixels"], cfg["camera_names"], device)

                if t % query_frequency == 0:
                    all_actions = policy(qpos, curr_image)
                if policy_config["temporal_agg"]:
                    all_time_actions[[t], t : t + num_queries] = all_actions
                    actions_for_curr_step = all_time_actions[:, t]
                    actions_populated = torch.all(actions_for_curr_step != 0, axis=1)
                    actions_for_curr_step = actions_for_curr_step[actions_populated]
                    k = 0.01
                    exp_weights = np.exp(-k * np.arange(len(actions_for_curr_step)))
                    exp_weights = exp_weights / exp_weights.sum()
                    exp_weights = (
                        torch.from_numpy(exp_weights.astype(np.float32))
                        .to(device)
                        .unsqueeze(dim=1)
                    )
                    raw_action = (actions_for_curr_step * exp_weights).sum(
                        dim=0, keepdim=True
                    )
                else:
                    raw_action = all_actions[:, t % query_frequency]

                ### post-process actions
                raw_action = raw_action.squeeze(0).cpu().numpy()
                action = post_process(raw_action)
                observation, reward, terminated, truncated, info = env.step(action)
    # action = pos2pwm(action).astype(int)
    # ### take action
    # follower.set_goal_pos(action)
