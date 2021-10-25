import yaml

from clients.pterodactyl import PterodactylClient


with open("config.yml", "r") as stream:
    config = yaml.safe_load(stream)

    PterodactylClient(
        config["pterodactyl"]["panel_url"],
        config["pterodactyl"]["api_key"],
        config["server"]["id"],
    )
