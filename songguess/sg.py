import os, asyncio
import math, random
from enum import Enum
from functools import wraps
from difflib import SequenceMatcher

import discord
from discord.ext import commands

from .player import MusicPlayer
from .queue import QuestionQueue
from .scoring import Scoring
from .gamers import Gamers


def _in_game_command(func):
    @wraps(func)
    async def wrap(self, ctx, *args, **kwargs):
        if not self.is_playing:
            await ctx.send(f"This command can only use in game running.")
            return
        if ctx.author.name not in self.gamers.info:
            await ctx.send(f"Please join the game first.")
            return
        await func(self, ctx, *args, **kwargs)
    return wrap


def _setting_command(func):
    @wraps(func)
    async def wrap(self, ctx, *args, **kwargs):
        if self.is_playing:
            await ctx.send(f"This command can only use when game is not running.")
            return
        await func(self, ctx, *args, **kwargs)
    return wrap


def _op_command(func):
    @wraps(func)
    async def wrap(self, ctx, *args, **kwargs):
        if ctx.author.name not in self.operator:
            await ctx.send(f"This command is a op command.")
            return
        await func(self, ctx, *args, **kwargs)
    return wrap


def _player_command(func):
    @wraps(func)
    async def wrap(self, ctx, *args, **kwargs):
        if not self.player.is_connected:
            await ctx.send("Please let bot join a voice channel first.")
            return
        await func(self, ctx, *args, **kwargs)
    return wrap


class SongGuess(commands.Cog):
    def __init__(self, bot, config, queue: QuestionQueue):
        self.bot = bot
        self.config = config
        
        # attribute
        self.support_starting_point = ["beginning", "intro", "chorus", "verse", "random"]
        self.support_scoring_mode = ["first-to-win", "timing-rush"]

        # bot config
        self.cache_folder = config.get("SongGuess", "cache_folder", fallback=os.path.join(os.path.dirname(__file__), "../cache"))
        
        # rule config
        self.ans_type = config.get("Rule", "answer_type", fallback="name")
        self.starting_point = config.get("Rule", "starting_point", fallback="beginning")
        if self.starting_point not in self.support_starting_point:
            print("error config in starting_point")
            self.starting_point = "beginning"
        self.scoring_mode = config.get("Rule", "scoring_mode", fallback="first-to-win")
        if self.scoring_mode not in self.support_scoring_mode:
            print("error config in scoring_mode")
            self.starting_point = "first-to-win"
        self.song_length = config.getint("Rule", "song_length", fallback=0)
        self.question_amount = config.getint("Rule", "question_amount", fallback=1)
        self.need_season = config.getboolean("Rule", "need_season", fallback=False)
        self.dup_anime = config.getboolean("Rule", "dup_anime", fallback=False)

        # initial objects
        self.player = MusicPlayer(self.cache_folder)
        self.qlist = queue
        self.gamers = Gamers()
        self.timer = None

        self.operator = []
        # game state
        self.is_playing = False
        self.running_channel = None
        # round state
        self.question = None
        self.answer = ""
        self.winners = []
        self.round_end = False

    async def _end_game(self, ctx):
        self.player.stop()
        
        for file in os.listdir(self.cache_folder):
            try:
                os.unlink(os.path.join(self.cache_folder, file))
            except Exception as e:
                print(f"Error trying to delete {file}: {str(e)}")
        
        await self._broadcast_msg("Game End!")
        
        # reset game state
        self.is_playing = False
        self.running_channel = None

    async def _start_round(self, ctx):
        self.question = await self.qlist.get_question()
        q = self.question
        
        if not q:
            await self._broadcast_msg("all question end.")
            await self._end_game(ctx)
            return
        
        if self.ans_type not in q.info:
            await self._broadcast_msg("無法取得答案，請確認 answer_type 是否設定正確")
            await self._end_game(ctx)
            return

        # reset game state
        if self.need_season:
            self.answer = q.info[self.ans_type] + q.info["season"]
        else:
            self.answer = q.info[self.ans_type]
        self.winners = []
        self.round_end = False
        
        start = self._get_song_start(q)
        length = self._get_song_play_time(q, start)
        
        embed = discord.Embed(title=f"Question {self.qlist.number} start!", color=MsgLevel.LEVEL2.value)
        await self._broadcast_msg(embed=embed)
        await self.player.play(q.song_info["path"], start, length)

    def _get_song_start(self, q):
        if self.starting_point == "beginning":
            return 0
        elif self.starting_point == "random":
            return math.floor(random.uniform(0, 0.9) * int(q.song_info["duration"]))
        else:
            return q.info.get(self.starting_point, 0)

    def _get_song_play_time(self, q, start):
        if start + self.song_length > int(q.song_info["duration"]):
            if start > int(q.song_info["duration"]):
                # Error on starting point of the question
                print(f"start point {start} is bigger than length of the song {int(q.song_info['duration'])}")
            return 0
        return self.song_length

    def _check_answer(self, str1, str2):
        return SequenceMatcher(None, str1.lower().replace(" ",""), str2.lower().replace(" ","")).ratio()

    def _startTimer(self):
        async def countdown():
            try:
                zh_num = 0
                other_num = 0 
                for ch in self.answer:
                    if ch >= "\u4E00" and ch <= "\u9FFF":
                        zh_num += 1
                    else:
                        other_num += 1
                sec = 5 + (zh_num * 1) + (other_num * 0.4)
                await asyncio.sleep(sec)

                self.round_end = True
                msg = f"回合結束！答案是 {self.answer}\n答對的人有："
                msg += ", ".join(self.winners)
                embed = discord.Embed(title=msg, color=MsgLevel.LEVEL5.value)
                await self._broadcast_msg(embed=embed)
            except asyncio.CancelledError:
                pass

        self.timer = self.bot.loop.create_task(countdown())

    async def _broadcast_msg(self, msg=None, exclusion=[], *, embed=None):
        assert self.is_playing
        assert self.running_channel is not None

        if self.scoring_mode == "first-to-win":
            await self.running_channel.send(msg, embed=embed)
        elif self.scoring_mode == "timing-rush":
            await self.gamers.send_to_all_gamers(msg, exclusion, embed=embed)

    """ ----------------- Game Control ----------------- """

    @commands.command()
    async def summon(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:
            await self.player.start(ctx.author.voice.channel)
        else:
            await ctx.send("Please join a voice channel first.")

    @commands.command()
    @_player_command
    async def disconnect(self, ctx):
        await self.player.close()

    @commands.command()
    @_op_command
    @_player_command
    async def play(self, ctx):
        if self.is_playing:
            await ctx.send("Game is already running.")
            return

        if ctx.channel.type != discord.ChannelType.text:
            await ctx.send("Please start game at text channel.")
            return

        await ctx.send("Game loading...")

        # reset game state
        self.gamers.reset_all_scores()
        self.is_playing = True
        self.running_channel = ctx.channel
        
        got = self.qlist.prepare(self.question_amount, self.dup_anime)
        if got < self.question_amount:
            await ctx.send(f"注意：符合條件的題目只有 {got} 題")

        await self._start_round(ctx)

    @commands.command(name="next", aliases=["n"])
    @_in_game_command
    @_op_command
    @_player_command
    async def next_round(self, ctx):
        if self.round_end:
            await self._start_round(ctx)

    @commands.command()
    @_in_game_command
    @_op_command
    @_player_command
    async def end(self, ctx):
        await self._end_game(ctx)

    @commands.command()
    @_in_game_command
    @_player_command
    async def replay(self, ctx):
        await self.player.replay()

    @commands.command()
    @_in_game_command
    @_op_command
    @_player_command
    async def replay_new(self, ctx):
        start = self._get_song_start(self.question)
        play_time = self._get_song_play_time(self.question, start)
        await self.player.play(self.question.song_info["path"], start, play_time)

    @commands.command()
    @_in_game_command
    @_player_command
    async def stop(self, ctx):
        await self.player.stop()

    @commands.command(aliases=["g"])
    @_in_game_command
    async def guess(self, ctx, *, answer):
        if self.scoring_mode == "first-to-win":
            if not self.round_end and self._check_answer(answer, self.answer) == 1.0:
                self.winners.append(ctx.author.name)
                self.gamers.add_points(ctx.author.name, 1)
                self.round_end = True
                embed = discord.Embed(title=f"{ctx.author.name} bingo! 答案是 {self.answer}", color=MsgLevel.LEVEL4.value)
                await ctx.send(embed=embed)
        elif self.scoring_mode == "timing-rush":
            if ctx.channel.type != discord.ChannelType.private:
                return
            if self.round_end:
                return
            if ctx.author.name in self.winners:
                return
            acc = self._check_answer(answer, self.answer)
            if acc == 1.0:
                self.winners.append(ctx.author.name)
                if len(self.winners) == len(self.gamers.info):
                    self.round_end = True
                    if self.timer:
                        self.timer.cancel()
                        self.timer = None
                # send message
                if len(self.gamers.info) > 1 and len(self.winners) == 1:
                    self.gamers.add_points(ctx.author.name, 2)
                    embed = discord.Embed(title=f"你答對了！", color=MsgLevel.LEVEL4.value)
                    await ctx.send(embed=embed)
                    embed = discord.Embed(title=f"有人答對了，開始倒數", color=MsgLevel.LEVEL1.value)
                    await self.gamers.send_to_all_gamers(exclusion=[ctx.author.name], embed=embed)
                    self._startTimer()
                else:
                    self.gamers.add_points(ctx.author.name, 1)
                    embed = discord.Embed(title=f"你答對了！", color=MsgLevel.LEVEL4.value)
                    await ctx.send(embed=embed)
                if len(self.winners) == len(self.gamers.info):
                    msg = f"所有人都答對了，答案是 {self.answer}\n回答順序："
                    msg += ", ".join(self.winners)
                    embed = discord.Embed(title=msg, color=MsgLevel.LEVEL5.value)
                    await self.gamers.send_to_all_gamers(embed=embed)
            elif acc > 0.5:
                embed = discord.Embed(title=f"{answer} 已經很接近了", color=MsgLevel.LEVEL3.value)
                await ctx.send(embed=embed)
            else:
                await self.gamers.send_to_all_gamers(f"{ctx.author.name} 猜 {answer}", [ctx.author.name])

    @commands.command(name="answer")
    @_in_game_command
    @_op_command
    async def show_answer(self, ctx):
        self.round_end = True
        await self._broadcast_msg(f"The answer is {self.answer}")

    @commands.command(name="qinfo")
    @_in_game_command
    @_op_command
    async def show_qinfo(self, ctx):
        if self.round_end:
            await ctx.send(f"{self.question.info}")

    """ ----------------- Rule Setting ----------------- """

    @commands.group(case_insensitive=True)
    async def rule(self, ctx):
        pass

    @rule.command(name="ans_type")
    @_setting_command
    async def set_ans_type(self, ctx, ans_type):
        at = ans_type.lower()
        self.ans_type = at
        await ctx.send(f"answer type is set to {at}")

    @rule.command(name="start_point")
    @_setting_command
    async def set_starting_point(self, ctx, start_point):
        sp = start_point.lower()
        if sp not in self.support_starting_point:
            await ctx.send(f"{sp} does not support")
            return
        
        self.starting_point = sp
        await ctx.send(f"song would start from {sp}")

    @rule.command(name="length")
    @_setting_command
    async def set_length(self, ctx, length):
        try:
            l = int(length)
        except ValueError:
            await ctx.send(f"length should be second (i.e. integer)")
        else:
            self.song_length = l
            await ctx.send(f"song length is set to {l}")

    @rule.command(name="amount")
    @_setting_command
    async def set_amount(self, ctx, amount):
        try:
            am = int(amount)
        except ValueError:
            await ctx.send(f"question amount should be integer")
        else:
            self.question_amount = am
            await ctx.send(f"question amount is set to {amount}")

    @rule.command(name="scoring_mode")
    @_setting_command
    async def set_scoring_mode(self, ctx, scoring_mode):
        sm = scoring_mode.lower()
        if sm not in self.support_scoring_mode:
            await ctx.send(f"{sm} does not support")
            return
        
        self.scoring_mode = sm
        await ctx.send(f"計分方式已設為 {sm}")

    @rule.command(name="need_season")
    @_setting_command
    async def set_need_season(self, ctx, enable):
        if enable.lower() not in ["true", "false"]:
            await ctx.send(f"{enable} 只能是 True 或 False")
            return

        self.need_season = True if enable.lower() == "true" else False
        if self.need_season:
            await ctx.send(f"答案格式已改成需要加上 season")
        else:
            await ctx.send(f"答案格式已改成不需加上 season")

    @rule.command(name="dup_anime")
    @_setting_command
    async def set_dup_anime(self, ctx, dup):
        if dup.lower() not in ["true", "false"]:
            await ctx.send(f"{dup} 只能是 True 或 False")
            return

        self.dup_anime = True if dup.lower() == "true" else False
        if self.dup_anime:
            await ctx.send(f"已允許題目有重複動畫")
        else:
            await ctx.send(f"已禁止題目有重複動畫")

    @rule.command(name="show")
    async def show_rule(self, ctx):
        msg = f"目前的規則：\n" \
              f"題數：{self.question_amount}\n" \
              f"要猜的欄位：{self.ans_type}\n" \
              f"計分方式：{self.scoring_mode}\n" \
              f"答案需要加上 season：{self.need_season}\n" \
              f"允許重複動畫：{self.dup_anime}\n" \
              f"歌曲開始播放位置：{self.starting_point}\n" \
              f"播放時間（0 表示不中斷）：{self.song_length}\n"
        await ctx.send(msg)

    """ ----------------- Scoring ----------------- """

    @commands.command()
    async def join(self, ctx):
        if self.gamers.check_if_gamer(ctx.author.name):
            await ctx.send(f"{ctx.author.name} is already a player.")
            return
        self.gamers.add(ctx.author)
        if not self.operator:
            self.operator.append(ctx.author.name)
        await ctx.send(f"{ctx.author.name} has joined.")

    @commands.command()
    async def leave(self, ctx):
        if not self.gamers.check_if_gamer(ctx.author.name):
            await ctx.send(f"Please join the game first.")
            return
        self.gamers.remove(ctx.author.name)
        if ctx.author.name in self.operator:
            self.operator.remove(ctx.author.name)
            if len(self.operator) == 0 and len(self.gamers.info) > 0:
                new_op = self.gamers.random_choose()
                self.operator.append(new_op)
                await ctx.send(f"new op is {new_op}")
        await ctx.send(f"{ctx.author.name} has left.")

    @commands.command()
    @_op_command
    async def kick(self, ctx, name):
        if not self.gamers.check_if_gamer(name):
            await ctx.send(f"{name} is not a player.")
            return
        self.gamers.remove(name)
        if name in self.operator:
            self.operator.remove(name)
            if len(self.operator) == 0 and len(self.gamers.info) > 0:
                new_op = self.gamers.random_choose()
                self.operator.append(new_op)
                await ctx.send(f"new op is {new_op}")
        await ctx.send(f"{name} has left.")

    @commands.command()
    async def scores(self, ctx):
        scores = self.gamers.get_all_scores()
        await ctx.send(f"{scores}")

    @commands.command()
    @_op_command
    async def add(self, ctx, player, points):
        try:
            self.gamers.add_points(player, points)
            await ctx.send(f"{player}: {self.gamers.get_score(player)}")
        except ValueError:
            await ctx.send(f"{player} is not a player")

    @commands.command()
    @_op_command
    async def minus(self, ctx, player, points):
        try:
            self.gamers.deduct_points(player, points)
            await ctx.send(f"{player}: {self.gamers.get_score(player)}")
        except ValueError:
            await ctx.send(f"{player} is not a player")

    @commands.command()
    @_op_command
    async def setpoint(self, ctx, player, point):
        try:
            self.gamers.set_score(player, point)
            await ctx.send(f"{player}: {self.gamers.get_score(player)}")
        except ValueError:
            await ctx.send(f"{player} is not a player")

    @commands.command()
    @_op_command
    async def resetpoint(self, ctx):
        self.gamers.reset_all_scores()
        await ctx.send(f"Points of all players have reset")

    """ ----------------- Op ----------------- """

    @commands.group(case_insensitive=True)
    async def op(self, ctx):
        pass

    @op.command(name="add")
    @_op_command
    async def op_add(self, ctx, name):
        if name not in self.gamers.info:
            await ctx.send(f"{name} is not a player")
            return
        self.operator.append(name)
        await ctx.send(f"{name} is a op now")

    @op.command(name="kick")
    @_op_command
    async def op_kick(self, ctx, name):
        if name not in self.operator:
            await ctx.send(f"{name} is not a op")
            return
        if len(self.operator) == 1:
            await ctx.send(f"{name} is the only op")
            return
        self.operator.remove(name)
        await ctx.send(f"{name} is not a op now")

    @op.command(name="list")
    async def op_list(self, ctx):
        await ctx.send(f"{self.operator}")


class MsgLevel(Enum):
    LEVEL1 = 0xff0000
    LEVEL2 = 0xffff00
    LEVEL3 = 0xff00ff
    LEVEL4 = 0x00ff00
    LEVEL5 = 0x0000ff
    LEVEL6 = 0x00ffff
