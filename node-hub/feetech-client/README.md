## FeetechClient for SCS/STS motors

This node is a client for the Feetech motors. It is based on the Dynamixel SDK and is used to control the motors. It
is a Python node that communicates with the motors via the USB port.

## YAML Configuration

```YAML
nodes:
  - id: feetech_client
    path: client.py # modify this to the relative path from the graph file to the client script
    inputs:
      pull_position: dora/timer/millis/10 # pull the present position every 10ms
      pull_velocity: dora/timer/millis/10 # pull the present velocity every 10ms
      pull_current: dora/timer/millis/10 # pull the present current every 10ms

      # write_goal_position: some goal position from other node

      # end: some end signal from other node
    outputs:
      - position # regarding 'pull_position' input, it will output the position every 10ms
      - velocity # regarding 'pull_velocity' input, it will output the velocity every 10ms
      - current # regarding 'pull_current' input, it will output the current every 10ms

    env:
      PORT: COM9 # e.g. /dev/ttyUSB0 or COM9
      CONFIG: config.json # the configuration file for the motors
```

## Arrow format

### Outputs

Arrow **Struct** of type:

```Python
pa.struct([
    pa.field("joints", pa.list_(pa.string())),
    pa.field("values", pa.list_(pa.int32()))
])
```

### Inputs

Arrow **Array** of type:

```Python
pa.struct([
    pa.field("joints", pa.list_(pa.string())),
    pa.field("values", pa.list_(pa.int32()))
])
```

**Note**: only the first element of the array is used, the rest are ignored.

## Configuration

The configuration file that should be passed to the node is a JSON file that contains the configuration for the motors:

```JSON
{
  "shoulder_pan": {
    "id": 1,
    "model": "scs_series",
    "torque": true
  }
}
```

The configuration file starts by the **joint** name of the servo. **id**: the id of the motor in the bus, **model**: the
model of the motor, **torque**: whether the motor should be in torque mode or not (at the beginning), **goal_current**:
the goal current for the motor at the beginning, null if you don't want to set it.

## License

This library is licensed under the [Apache License 2.0](../../LICENSE).