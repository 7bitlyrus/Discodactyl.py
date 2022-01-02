import yaml

with open("config.yml", "r") as stream:
    config = yaml.safe_load(stream)