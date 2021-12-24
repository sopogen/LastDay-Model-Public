from pathlib import Path
import os
import yaml


def load_yaml(filename, env):
    abs_dir = os.path.dirname(__file__)

    with Path(f"{abs_dir}/{filename}.yaml").open() as file:
        config = yaml.load(file, Loader=yaml.FullLoader)[env]
    return config


CONFIG = load_yaml('config', 'dev')
