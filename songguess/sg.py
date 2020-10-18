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
        self.support_starting_point = ["beginning", "intro", "chorus", "verse"]

        # bot config
        self.cache_folder = config.get("Bot", "cache_folder", fallback=os.path.join(os.path.dirname(__file__), "../cache"))
        
        # rule config
        self.ans_type = config.get("Rule", "answer_type", fallback="name")
        if self.ans_type not in self.support_answer_type:
            print("error config in answer_type")
            self.ans_type = "name"
        self.starting_point = config.get("Rule", "starting_point", fallback="beginning")
        if self.starting_point not in self.support_starting_point:
            print("error config in starting_point")
            self.starting_point = "beginning"
        self.song_length = config.getint("Rule", "song_length", fallback=0)
        self.question_amount = config.getint("Rule", "question_amount", fallback=1)

        # initial objects
        self.player = MusicPlayer(self.cache_folder)
        self.qdb = FirestoreQDB()
        self.qlist = QuestionQueue()
        self.scoring = Scoring()

        bot.add_cog(self.scoring)

    async def _end_game(self, ctx):
        if self.player.is_running:
            await self.player.stop_and_delete()
        
        for file in os.listdir(self.cache_folder):
            try:
                os.unlink(os.path.join(self.cache_folder, file))
            except Exception as e:
                print(f"Error trying to delete {file}: {str(e)}")
        
        self.is_playing = False
        await ctx.send("Game End!")

    async def _start_round(self, ctx):
        q = await self.qlist.get_question()
        if not q:
            await ctx.send("all question end.")
            await self._end_game(ctx)
            return
        
        self.scoring.now_answer = q.info[self.ans_type]
        start = q.info.get(self.starting_point, 0)
        length = self.song_length
        if start + length > int(q.task.result()["duration"]):
            if start > int(q.task.result()["duration"]):
                print(f"start point {start} is bigger than length of the song {int(q.task.result()['duration'])}")
            length = 0
        
        await self.player.play(f'{q.task.result()["id"]}.opus', start, length)
        await ctx.send("New round start!")

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
            await ctx.send("Game is running.")
            return
        
        if not self.player.is_running:
            await ctx.send("Please let bot join a voice channel first.")
            return

        await ctx.send("Game loading...")

        self.scoring.reset()
        self.is_playing = True
        self.qlist.prepare(self.qdb, self.bot.loop)

        await ctx.send("Game start!")

        await self._start_round(ctx)

    @commands.command(name="next")
    async def next_round(self, ctx):
        if not self.is_playing:
            await ctx.send("Game is not running.")
            return

        if not self.player.is_running:
            await ctx.send("Please let bot join a voice channel first.")
            return

        await self._start_round(ctx)

    @commands.command()
    async def end(self, ctx):
        if not self.is_playing:
            await ctx.send("Game is not running.")
            return

        await self._end_game(ctx)

    @commands.command()
    async def replay(self, ctx):
        await self.player.replay()

    @commands.command()
    async def stop(self, ctx):
        await self.player.stop()

    @commands.group(case_insensitive=True)
    async def rule(self, ctx):
        pass

    @rule.command(name="ans_type")
    async def set_ans_type(self, ctx, ans_type):
        at = ans_type.lower()
        if at not in self.support_answer_type:
            await ctx.send(f"{at} does not support")
            return
        
        self.ans_type = at
        await ctx.send(f"answer type is set to {at}")

    @rule.command(name="start_point")
    async def set_starting_point(self, ctx, start_point):
        sp = start_point.lower()
        if sp not in self.support_starting_point:
            await ctx.send(f"{sp} does not support")
            return
        
        self.starting_point = sp
        await ctx.send(f"song would start from {sp}")

    @rule.command(name="length")
    async def set_length(self, ctx, length):
        try:
            l = int(length)
        except ValueError:
            await ctx.send(f"length should be second (i.e. integer)")
        else:
            self.song_length = l
            await ctx.send(f"song length is set to {l}")

    @rule.command(name="amount")
    async def set_amount(self, ctx, amount):
        try:
            am = int(amount)
        except ValueError:
            await ctx.send(f"question amount should be integer")
        else:
            self.question_amount = am
            await ctx.send(f"question amount is set to {amount}")

    # TODO: 有人答對自動切題（`auto/auto_count`）

    @rule.command(name="show")
    async def show_rule(self, ctx):
        msg = f"Rule:\n" \
              f"Question amount: {self.question_amount}\n" \
              f"Answer type: {self.ans_type}\n" \
              f"Starting point of songs: {self.starting_point}\n" \
              f"Song length: {self.song_length}\n"
        await ctx.send(msg)

