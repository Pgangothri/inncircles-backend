import os
import yaml

def load_config(filename: str) -> dict:
    path = os.path.join("config", filename)
    with open(path, "r") as f:
        return yaml.safe_load(f)
