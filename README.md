# `dora-rs` powered arms!

This repo will contain all application related to dora-rs powered robots.

## [Trossen Robotics - Aloha v2](aloha/README.md)

### Teleop Getting started

```bash
cargo run -p aloha-teleop --release

## For configuration
# cargo run -p aloha-teleop -- --help
```

### Model evaluation

To evaluate a model checkpoint you can use:

```bash
dora start aloha/graphs/eval.yml --attach
```

Within the dataflow, you can specify the model you want to use within the eval node:

```yaml
- id: eval
  custom:
    source: python
    args: /path/to/lerobot/lerobot/scripts/eval.py -p cadene/aloha_act_no_state_aloha_v2_static_dora_test_wrist_gripper eval.n_episodes=1 eval.batch_size=1 env.episode_length=20000
    inputs:
      agent_pos: aloha-client/puppet_position
      cam_left_wrist: cam_left_wrist/image
      cam_right_wrist: cam_right_wrist/image
      cam_low: cam_low/image
      cam_high: cam_high/image
    outputs:
      - action
```

## [Tau Robotics - Low Cost Robot](alexk_low_cost_robot/README.md)

### Teleop Getting started

```bash
cargo run -p lcr-teleop --release

## For configuration
cargo run -p lcr-teleop -- --help
```

## [Pollen Robotics - Reachy2](reachy/README.md)

### Evaluation Getting started

```bash
dora start reachy/graphs/eval.yml --attach
```

## License

This library is licensed under the [Apache License 2.0](./LICENSE).
