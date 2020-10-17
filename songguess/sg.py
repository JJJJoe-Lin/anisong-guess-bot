import os

import discord
from discord.ext import commands

from .player import MusicPlayer

class SongGuess(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

        self.questions = []
        self.player = MusicPlayer("./cache")

    @commands.command()
    async def summon(self, ctx: commands.Context):
        if ctx.author.voice.channel:
            await self.player.start(ctx.author.voice.channel)
        else:
            await ctx.send("Please join a voice channel first.")

    @commands.command()
    async def disconnect(self, ctx: commands.Context):
        await self.player.close()

    @commands.command()
    async def play(self, ctx):
        # TODO: 自符合條件的題目集隨機選題
        # TODO: 將題目交付給下載器
        # TODO: 當有題目準備完成，交給播放器播放
        pass

    @commands.command()
    async def stop(self, ctx):
        await self.player.stop()
        