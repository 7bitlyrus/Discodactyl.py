import discord
import yaml
import logging
from discord.ext import commands

from .pterodactyl import PterodactylClient

logging.basicConfig(level=logging.INFO)

with open("config.yml", "r") as stream:
    config = yaml.safe_load(stream)

bot = commands.Bot(
    command_prefix=commands.when_mentioned,
    case_insensitive=True,
    intents=discord.Intents(messages=True),
)

pterodactyl = PterodactylClient(
    config["pterodactyl"]["panel_url"],
    config["pterodactyl"]["api_key"],
    config["server"]["id"],
)


class Bridge(commands.Cog):
    def __init__(self, bot):
        self.task = bot.loop.create_task(pterodactyl.start())  # TODO: CLOSE TASK AND ONLY START ONCE, ETC ,ETC

    def cog_unload(self):
        self.task.cancel()

    @commands.Cog.listener()
    async def on_message(message):
        print('[discord] on_message:', message.content)

    @pterodactyl.on('stats')
    async def test(data):
        print(data)

    @pterodactyl.on('console output')
    async def output(data):
        await pterodactyl.send('send command', f'say {data}')


bot.add_cog(Bridge(bot))
bot.load_extension('jishaku')

bot.run(config['discord-token'])