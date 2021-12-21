import asyncio
import logging

import discord
import yaml

from clients.pterodactyl import PterodactylClient


logging.basicConfig(level=logging.INFO)

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
    asyncio.create_task(ps.start())  # TODO: CLOSE TASK AND ONLY START ONCE, ETC ,ETC
    print('[discord] on_ready')


@client.event
async def on_message(message):
    print('[discord] on_message:', message.content)
    await ps.send('send command', [f'say {message.content}'])


client.run(config['discord-token'])
