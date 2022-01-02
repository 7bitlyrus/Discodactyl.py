import logging
import yaml

from discord.ext import commands

from .pterodactyl import PterodactylClient
from .utils import quit_on_exception

with open("config.yml", "r") as stream:
    config = yaml.safe_load(stream)

pterodactyl = PterodactylClient(
    panel_url=config["pterodactyl"]["panel_url"],
    api_key=config["pterodactyl"]["api_key"],
    server_id=config["pterodactyl"]["server_id"],
)

logger = logging.getLogger(__name__)


class Bridge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.task = bot.loop.create_task(quit_on_exception(pterodactyl.start()))

    def cog_unload(self):
        self.task.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        logger.info('on_message:' + message.content)
        pass

    @pterodactyl.on('stats')
    async def test(data):
        logger.info('stats:' + str(data))
        pass


def setup(bot):
    bot.add_cog(Bridge(bot))


def teardown(bot):
    bot.remove_cog('Bridge')