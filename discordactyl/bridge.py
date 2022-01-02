import logging
from discord.ext import commands

from .config import config
from .pterodactyl import PterodactylClient
from .utils import quit_on_exception

logger = logging.getLogger(__name__)

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