import asyncio
import logging

import discord
import yaml

from clients.pterodactyl import PterodactylClient


with open("config.yml", "r") as stream:
    config = yaml.safe_load(stream)

    ps = PterodactylClient(
        config["pterodactyl"]["panel_url"],
        config["pterodactyl"]["api_key"],
        config["server"]["id"],
    )

client = discord.Client()


@client.event
async def on_ready():
    print('[discord] on_ready')


@client.event
async def on_message(message):
    print('[discord] on_message:', message.content)


async def main():
    await asyncio.gather(ps.start(), client.start(config['discord-token']))


asyncio.run(main())
