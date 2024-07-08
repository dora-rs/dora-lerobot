## Replay

This node is a replay client.

## YAML Configuration

````YAML
nodes:
  - id: replay_client
    path: client.py # modify this to the relative path from the graph file to the client script
    inputs:
      pull_position: dora/timer/millis/10

    outputs:
      - position

    env:
      PATH: /path/to/record
      EPISODE: 1
````

## License

This library is licensed under the [Apache License 2.0](../../LICENSE).