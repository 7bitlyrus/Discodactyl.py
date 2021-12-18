# https://stackoverflow.com/a/66249833
# https://betterprogramming.pub/a-deeper-look-at-async-and-concurrent-programming-in-python-9f2a84adbdd2

import yaml
import websockets
import discord
import asyncio

from clients.pterodactyl import PterodactylClient

with open("config.yml", "r") as stream:
    config = yaml.safe_load(stream)

# ==== Discord Setup ====
client = discord.Client()


@client.event
async def on_ready():
    print('[discord] on_ready')


@client.event
async def on_message(message):
    print('[discord] on_message:', message.content)


# ==== Websocket Setup ====

ptero = PterodactylClient(
    config["pterodactyl"]["panel_url"],
    config["pterodactyl"]["api_key"],
    config["server"]["id"],
)


async def websocket():
    # _, websocket_url = await ptero._fetch_websocket_credentials()
    websocket_url = 'wss://demo.piesocket.com/v3/channel_1?api_key=oCdCMcMPQpbvNjUIzqtvF1d2X2okWpDQj4AwARJuAgtjhzKxVEjQU6IdCjwm&notify_self'
    async with websockets.connect(websocket_url, origin='piesocket.com') as websocket:
        print('[websocket] ready')
        print(websocket_url)
        while True:
            try:
                # h = await asyncio.wait_for(websocket.recv(), timeout=1)
                h = await websocket.recv()
                print(f'[ws] {h}')

            except Exception as e:
                # print(f'[ws] !! {e}')
                pass

            # await asyncio.sleep(1)


# ==== Startup ====
# asyncio.get_event_loop().run_until_complete(websocket())
# client.run(config['discord-token'])


async def main():
    await asyncio.gather(websocket(), client.start(config['discord-token']))


asyncio.run(main())