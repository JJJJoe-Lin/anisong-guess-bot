from functools import wraps

from discord.ext import commands

def _need_join(func):
    @wraps(func)
    async def wrap(self, ctx, *args, **kwargs):
        if ctx.author.name not in self.player_info:
            await ctx.send(f"Please join the game first.")
            return
        await func(self, ctx, *args, **kwargs)
    return wrap

class Scoring(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.player_info = {}
    
    def _add_point(self, player, point):
        self.player_info[player] += point

    def _set_point(self, player, point):
        self.player_info[player] = point

    def _reset_point(self):
        for player in self.player_info:
            self.player_info[player] = 0

    @commands.command()
    @_need_join
    async def add(self, ctx, player, point):
        self._add_point(player, point)
        await ctx.send(f"{player}: {self.player_info['player']}")

    @commands.command()
    @_need_join
    async def setpoint(self, ctx, player, point):
        self._set_point(player, point)
        await ctx.send(f"{player}: {self.player_info['player']}")

    @commands.command()
    @_need_join
    async def resetpoint(self, ctx):
        self._reset_point()
        await ctx.send(f"Points of all players have reset")

    @commands.command()
    async def join(self, ctx):
        if ctx.author.name in self.player_info:
            await ctx.send(f"{ctx.author.name} is already a player.")
            return
        self.player_info[ctx.author.name] = 0
        await ctx.send(f"{ctx.author.name} has joined.")

    @commands.command()
    @_need_join
    async def leave(self, ctx):
        del self.player_info[ctx.author.name]
        await ctx.send(f"{ctx.author.name} has left.")

    @commands.command()
    @_need_join
    async def scores(self, ctx):
        await ctx.send(f"{self.player_info}")
    