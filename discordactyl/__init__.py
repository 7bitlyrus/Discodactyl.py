import logging

import discord
import yaml
from discord.ext import commands

logging.basicConfig(level=logging.INFO)

with open("config.yml", "r") as stream:
    config = yaml.safe_load(stream)

intents = discord.Intents(guilds=True, messages=True)
bot = commands.Bot(command_prefix=commands.when_mentioned, case_insensitive=True, intents=intents)


bot.load_extension('jishaku')
bot.load_extension('discordactyl.bridge')

bot.run(config['discord']['token'])
