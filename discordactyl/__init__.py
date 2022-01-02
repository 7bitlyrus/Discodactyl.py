import logging

import discord
import yaml
from discord.ext import commands

from .pterodactyl import PterodactylClient
from .utils import quit_on_exception


logging.basicConfig(level=logging.INFO)

with open("config.yml", "r") as stream:
    config = yaml.safe_load(stream)

intents = discord.Intents(guilds=True, messages=True)
bot = commands.Bot(command_prefix=commands.when_mentioned, case_insensitive=True, intents=intents)

pterodactyl = PterodactylClient(
    panel_url=config["pterodactyl"]["panel_url"],
    api_key=config["pterodactyl"]["api_key"],
    server_id=config["pterodactyl"]["server_id"],
)


class Bridge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.task = bot.loop.create_task(quit_on_exception(pterodactyl.start()))

    def cog_unload(self):
        self.task.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        # print('[discord] on_message:', message.content)
        pass

    @pterodactyl.on('stats')
    async def test(data):
        # print(data)
        pass


bot.add_cog(Bridge(bot))
bot.load_extension('jishaku')

bot.run(config['discord']['token'])
