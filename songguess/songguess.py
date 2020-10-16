import os

import discord
from discord.ext import commands

class SongGuess(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config