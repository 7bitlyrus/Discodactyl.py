import logging

import discord
import yaml
from discord.ext import commands

from .config import config

logging.basicConfig(level=logging.INFO)


intents = discord.Intents(guilds=True, messages=True)
bot = commands.Bot(command_prefix=commands.when_mentioned, case_insensitive=True, intents=intents)

bot.load_extension('jishaku')
bot.load_extension('discordactyl.bridge')

bot.run(config['discord']['token'])
