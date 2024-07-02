## DynamixelClient for XL motors

This node is a client for the Dynamixel motors. It is based on the Dynamixel SDK and is used to control the motors. It
is a Python node that communicates with the motors via the USB port.

## YAML Configuration

````YAML
nodes:
  - id: dynamixel_client
    path: client.py # modify this to the relative path from the graph file to the client script
    inputs:
      pull_position: dora/timer/millis/10 # pull the present position every 10ms
      pull_velocity: dora/timer/millis/10 # pull the present velocity every 10ms
      pull_current: dora/timer/millis/10 # pull the present current every 10ms

      # write_goal_position: some goal position from other node
      # write_goal_current: some goal current from other node
    outputs:
      - position # regarding 'pull_position' input, it will output the position every 10ms
      - velocity # regarding 'pull_velocity' input, it will output the velocity every 10ms
      - current # regarding 'pull_current' input, it will output the current every 10ms

    env:
      PORT: COM9 # e.g. /dev/ttyUSB0 or COM9
      
      IDS: 1 2 3 4 5 6
      JOINTS: shoulder_pan shoulder_lift elbow_flex wrist_flex wrist_roll gripper
      MODELS: x_series x_series x_series x_series x_series x_series

      TORQUE: True True True True True True

      INITIAL_GOAL_POSITION: None None None None None None
      INITIAL_GOAL_CURRENT: None None None None None 500

      OFFSETS:  -2048 2048 2048 2048 1024 2048
      DRIVE_MODES:  POS NEG NEG NEG NEG NEG
````

## License

This library is licensed under the [Apache License 2.0](../../LICENSE).