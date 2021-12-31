import logging

import discord
import yaml
from discord.ext import commands

from .pterodactyl import PterodactylClient


logging.basicConfig(level=logging.INFO)

with open("config.yml", "r") as stream:
    config = yaml.safe_load(stream)

intents = discord.Intents(guilds=True, messages=True)
bot = commands.Bot(command_prefix=commands.when_mentioned, case_insensitive=True, intents=intents)

pterodactyl = PterodactylClient(
    config["pterodactyl"]["panel_url"],
    config["pterodactyl"]["api_key"],
    config["server"]["id"],
)


class Bridge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.task = bot.loop.create_task(pterodactyl.start())

    def cog_unload(self):
        self.task.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        print('[discord] on_message:', message.content)

    @pterodactyl.on('stats')
    async def test(data):
        print(data)


bot.add_cog(Bridge(bot))
bot.load_extension('jishaku')

bot.run(config['discord-token'])
