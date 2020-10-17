import os

import discord
from discord.ext import commands

from .player import MusicPlayer
from .db import FirestoreQDB
from .queue import QuestionQueue
from .scoring import Scoring

class SongGuess(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.is_playing = False
        self.support_answer_type = ["name", "singer", "year"]
        self.player = MusicPlayer("./cache")
        self.qdb = FirestoreQDB()
        self.qlist = QuestionQueue()
        self.scoring = Scoring()

        bot.add_cog(self.scoring)

        # apply config
        self.ans_type = config.get("Rule", "answer_type", fallback="name")
        if self.ans_type not in self.support_answer_type:
            print("error config in answer_type")
            self.ans_type = "name"

    @commands.command()
    async def summon(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:
            await self.player.start(ctx.author.voice.channel)
        else:
            await ctx.send("Please join a voice channel first.")

    @commands.command()
    async def disconnect(self, ctx):
        await self.player.close()

    @commands.command()
    async def play(self, ctx):
        if self.is_playing:
            return
        
        if not self.player.isRunning:
            await ctx.send("Please let bot join a voice channel first.")
            return

        self.scoring.reset()
        self.is_playing = True
        self.qlist.prepare(self.qdb, self.bot.loop)

        q = await self.qlist.get_question()
        if not q:
            await ctx.send("all question end.")
            self.is_playing = False
            return
        print(q.task.result())
        self.scoring.now_answer = q.info[self.ans_type]
        await self.player.play(f'{q.task.result()}.mp3', 0, 0)
        
        await ctx.send("Game start!")

    @commands.command()
    async def next(self, ctx):
        if not self.is_playing:
            return

        if not self.player.isRunning:
            await ctx.send("Please let bot join a voice channel first.")
            return

        q = await self.qlist.get_question()
        if not q:
            await ctx.send("all question end.")
            self.is_playing = False
            return
        self.scoring.now_answer = q.info[self.ans_type]
        await self.player.play(f'{q.task.result()}.mp3', 0, 0)

    @commands.command()
    async def stop(self, ctx):
        await self.player.stop()

    @commands.command()
    async def listAnswerType(self, ctx):
        await ctx.send(", ".join(self.support_answer_type))

    @commands.command()
    async def setAnswerType(self, ctx, ans_type):
        if ans_type not in self.support_answer_type:
            await ctx.send(f"{ans_type} does not support")
            return
        
        self.ans_type = ans_type
        await ctx.send(f"answer type is set to {ans_type}")
        