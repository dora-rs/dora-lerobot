from gym_dora.gym_dora.robots import aloha2, koch, reachy2
from gymnasium.envs.registration import register

register(
    id="gym_dora/DoraAloha2-v0",
    entry_point="gym_dora.env:DoraEnv",
    max_episode_steps=300,
    nondeterministic=True,
    kwargs={
        "fps": aloha2.FPS,
        "actions": aloha2.ACTIONS,
        "joints": aloha2.JOINTS,
        "cameras": aloha2.CAMERAS,
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
