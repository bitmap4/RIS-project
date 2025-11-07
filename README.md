# RIS Project

## Running the Demonstrations

To run the protocol demonstration, ensure you have Python installed along with the required libraries (as mentioned in `pyproject.toml`). You can execute the `protocol_demo.py` script located in the `demonstration` directory.

```bash
python -m demonstration all
```

or through uv:

```bash
uv sync # install dependencies
uv run python -m demonstration
```
This will simulate the interactions between the Vehicle, Fog Node, and Cloud Server, showcasing the registration and authentication phases of the protocol.

For running individual demonstrations:
```bash
python -m demonstration protocol
python -m demonstration security
python -m demonstration attacks
```
or through uv:
```bash
uv run python -m demonstration protocol
uv run python -m demonstration security
uv run python -m demonstration attacks
```

## Running Simulations and Benchmarks

```bash
cd simulations/docker
docker compose up --build
```

## Generating Demonstration Images

```bash
cd visualizations

python protocol_animation.py
# or with uv
uv run protocol_animation.py
```

## Scheme code

The core scheme implementation is located in the `scheme` directory, containing modules for the Cloud Server (`cs.py`), Fog Node (`fog_node.py`), and Vehicle (`vehicle.py`). Each module implements the respective functionalities as per the protocol.