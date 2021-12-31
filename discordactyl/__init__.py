import asyncio
import logging

import discord
import yaml

from .pterodactyl import PterodactylClient


logging.basicConfig(level=logging.INFO)

with open("config.yml", "r") as stream:
    config = yaml.safe_load(stream)

    pterodactyl = PterodactylClient(
        config["pterodactyl"]["panel_url"],
        config["pterodactyl"]["api_key"],
        config["server"]["id"],
    )

client = discord.Client()


@client.event
async def on_ready():
    asyncio.create_task(pterodactyl.start())  # TODO: CLOSE TASK AND ONLY START ONCE, ETC ,ETC
    print('[discord] on_ready')


@client.event
async def on_message(message):
    print('[discord] on_message:', message.content)
    # await pterodactyl.send('send command', [f'say {message.content}'])

    # await pterodactyl.close()


@pterodactyl.on('stats')
async def test(data):
    print(data)


@pterodactyl.on('console output')
async def output(data):
    await pterodactyl.send('send command', f'say {data}')


client.run(config['discord-token'])
# asyncio.run(pterodactyl.start())
