# Dora-LeRobot Node Hub

This hub contains all the non-specific nodes that are used by the robots in the Dora-LeRobot repository.

# Structure

The structure of the node hub is as follows (please use the same structure if you need to add a new node):

```
node-hub/
└── a-node/
    ├── main.py
    ├── README.mdr
    └── pyproject.toml
```

The idea is to make a `pyproject.toml` file that will install the required dependencies for the node **and** attach main
function of the node inside a callable script in your environment.

To do so, you will need to add a `main` function inside the `main.py` file.

```python
def main():
    pass
```

And then you will need to adapt the following `pyproject.toml` file:

```toml

[tool.poetry]
name = "[name of the node e.g. video-encoder]"
version = "0.1"
authors = ["[Pseudo/Name] <[email]>"]
description = "Dora Node for []"
readme = "README.md"

packages = [
    { include = "main.py", to = "[name of the node]" }
]

[tool.poetry.dependencies]
dora-rs = "0.3.5"

[tool.poetry.scripts]
[name of the node] = "[name of the node].main:main"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```

Finally, the README.md file should explicit all inputs/outputs of the node and how to configure it in the YAML file.

## License

This library is licensed under the [Apache License 2.0](../../LICENSE).