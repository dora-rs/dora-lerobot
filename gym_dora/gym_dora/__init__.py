from gym_dora.robots import aloha, koch, reachy2, reachy1
from gymnasium.envs.registration import register

register(
    id="gym_dora/DoraAloha-v0",
    entry_point="gym_dora.env:DoraEnv",
    max_episode_steps=300,
    nondeterministic=True,
    kwargs={
        "fps": aloha.FPS,
        "actions": aloha.ACTIONS,
        "joints": aloha.JOINTS,
        "cameras": aloha.CAMERAS,
    },
)

register(
    id="gym_dora/DoraKoch-v0",
    entry_point="gym_dora.env:DoraEnv",
    max_episode_steps=300,
    nondeterministic=True,
    kwargs={
        "fps": koch.FPS,
        "actions": koch.ACTIONS,
        "joints": koch.JOINTS,
        "cameras": koch.CAMERAS,
    },
)


register(
    id="gym_dora/DoraReachy2-v0",
    entry_point="gym_dora.env:DoraEnv",
    max_episode_steps=300,
    nondeterministic=True,
    kwargs={
        "fps": reachy2.FPS,
        "actions": reachy2.ACTIONS,
        "joints": reachy2.JOINTS,
        "cameras": reachy2.CAMERAS,
    },
)


register(
    id="gym_dora/DoraReachy1-v0",
    entry_point="gym_dora.env:DoraEnv",
    max_episode_steps=300,
    nondeterministic=True,
    kwargs={
        "fps": reachy1.FPS,
        "actions": reachy1.ACTIONS,
        "joints": reachy1.JOINTS,
        "cameras": reachy1.CAMERAS,
    },
)
