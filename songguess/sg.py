import os
import math, random
from functools import wraps

from discord.ext import commands

from .player import MusicPlayer
from .queue import QuestionQueue
from .scoring import Scoring

def _in_game_command(func):
    @wraps(func)
    async def wrap(self, ctx, *args, **kwargs):
        if not self.is_playing:
            await ctx.send(f"This command can only use in game running.")
            return
        if ctx.author.name not in self.player_info:
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

def _scoring_command(func):
    @wraps(func)
    async def wrap(self, ctx, *args, **kwargs):
        if ctx.author.name not in self.player_info:
            await ctx.send(f"Please join the game first.")
            return
        if self.scoring_mode != "manual":
            await ctx.send(f"This command can only use in manual scoring mode.")
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
        self.support_scoring_mode = ["manual", "first-to-win"]

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

        # initial objects
        self.player = MusicPlayer(self.cache_folder)
        self.qlist = queue

        # game state
        self.is_playing = False
        self.answer = ""
        self.winners = []
        self.player_info = {}

    async def _end_game(self, ctx):
        # self.player.stop_and_delete()
        self.player.stop()
        
        for file in os.listdir(self.cache_folder):
            try:
                os.unlink(os.path.join(self.cache_folder, file))
            except Exception as e:
                print(f"Error trying to delete {file}: {str(e)}")
        
        # reset game state
        self.answer = ""
        self.is_playing = False
        self.winners = []
        
        await ctx.send("Game End!")

    async def _start_round(self, ctx):
        q = await self.qlist.get_question()
        if not q:
            await ctx.send("all question end.")
            await self._end_game(ctx)
            return
        
        if self.ans_type not in q.info:
            await ctx.send("無法取得答案，請確認 answer_type 是否設定正確")
            await self._end_game(ctx)
            return

        # reset game state
        if self.need_season:
            self.answer = q.info[self.ans_type] + q.info["season"]
        else:
            self.answer = q.info[self.ans_type]
        self.winners = []
        
        if self.starting_point == "beginning":
            start = 0
        elif self.starting_point == "random":
            start = math.floor(random.uniform(0, 0.9) * int(q.task.result()["duration"]))
        else:
            start = q.info.get(self.starting_point, 0)

        length = self.song_length
        if start + length > int(q.task.result()["duration"]):
            if start > int(q.task.result()["duration"]):
                print(f"start point {start} is bigger than length of the song {int(q.task.result()['duration'])}")
            length = 0
        
        # await self.player.play(f'{q.task.result()["id"]}.opus', start, length)
        await self.player.play(q.task.result()["path"], start, length)
        await ctx.send("New round start!")

    def _check_answer(self, str1, str2):
        return str1.lower().replace(" ","") == str2.lower().replace(" ","")

    """ Game Control """

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
    @_player_command
    async def play(self, ctx):
        if self.is_playing:
            await ctx.send("Game is already running.")
            return

        await ctx.send("Game loading...")

        # reset game state
        self._reset_point()
        self.is_playing = True
        
        got = self.qlist.prepare(self.question_amount)
        if got < self.question_amount:
            await ctx.send(f"注意：符合條件的題目只有 {got} 題")

        await self._start_round(ctx)

    @commands.command(name="next", aliases=["n"])
    @_in_game_command
    @_player_command
    async def next_round(self, ctx):
        await self._start_round(ctx)

    @commands.command()
    @_in_game_command
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
    @_player_command
    async def stop(self, ctx):
        await self.player.stop()

    @commands.command(aliases=["g"])
    @_in_game_command
    async def guess(self, ctx, *, answer):
        if self.scoring_mode == "manual":
            await ctx.send(f"{self.scoring_mode} 模式下請自己對答案")
            return
        if not self.winners and self._check_answer(answer, self.answer):
            self._add_point(ctx.author.name, 1)
            self.winners.append(ctx.author.name)
            await ctx.send(f"{ctx.author.name} bingo!")
            # self.next_round()

    @commands.command(name="answer")
    @_in_game_command
    async def show_answer(self, ctx):
        if self.scoring_mode == "first-to-win":
            if "PC" not in self.winners:
                self.winners.append("PC")
        await ctx.send(f"The answer is {self.answer}")

    """ Rule Setting """

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

    # TODO: 有人答對自動切題（`auto/auto_count`）

    @rule.command(name="show")
    async def show_rule(self, ctx):
        msg = f"目前的規則：\n" \
              f"題數：{self.question_amount}\n" \
              f"要猜的欄位：{self.ans_type}\n" \
              f"計分方式：{self.scoring_mode}\n" \
              f"答案需要加上 season：{self.need_season}\n" \
              f"歌曲開始播放位置：{self.starting_point}\n" \
              f"播放時間（0 表示不中斷）：{self.song_length}\n"
        await ctx.send(msg)

    """ Scoring """

    @commands.command()
    async def join(self, ctx):
        if ctx.author.name in self.player_info:
            await ctx.send(f"{ctx.author.name} is already a player.")
            return
        self.player_info[ctx.author.name] = 0
        await ctx.send(f"{ctx.author.name} has joined.")

    @commands.command()
    async def leave(self, ctx):
        if ctx.author.name not in self.player_info:
            await ctx.send(f"Please join the game first.")
            return
        del self.player_info[ctx.author.name]
        await ctx.send(f"{ctx.author.name} has left.")

    @commands.command()
    async def scores(self, ctx):
        await ctx.send(f"{self.player_info}")

    def _add_point(self, player, point):
        self.player_info[player] += point

    def _set_point(self, player, point):
        self.player_info[player] = point

    def _reset_point(self):
        for player in self.player_info:
            self.player_info[player] = 0

    @commands.command()
    @_scoring_command
    async def add(self, ctx, player, point):
        self._add_point(player, int(point))
        await ctx.send(f"{player}: {self.player_info[player]}")

    @commands.command()
    @_scoring_command
    async def setpoint(self, ctx, player, point):
        self._set_point(player, int(point))
        await ctx.send(f"{player}: {self.player_info[player]}")

    @commands.command()
    @_scoring_command
    async def resetpoint(self, ctx):
        self._reset_point()
        await ctx.send(f"Points of all players have reset")
