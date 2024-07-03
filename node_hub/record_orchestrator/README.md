## Record Orchestrator

This node is responsible for orchestrating the record of data: it uses the Pygame interface node and send signals
to the rest of dataflow: episode recording, episode index, failed episode, etc.

## YAML Configuration

````YAML
nodes:
  - id: record_orchestrator
    path: ../../../node_hub/record_orchestrator/record.py
    inputs:
      key_pressed: pygame_interface/key_pressed
      
    outputs:
      - text
      - episode
      - failed
````

## License

This library is licensed under the [Apache License 2.0](../../LICENSE).