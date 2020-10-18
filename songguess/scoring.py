import discord
from discord.ext import commands

class Scoring(commands.Cog):
    def __init__(self):
        self.player_score = {}
        self.now_answer = ""
        pass
    
    def _add_point(self, player, point):
        self.player_score[player] += point

    def _set_point(self, player, point):
        self.player_score[player] = point

    def _reset_point(self):
        for player in self.player_score:
            self.player_score[player] = 0
    
    def reset(self):
        self._reset_point()
        self.now_answer = ""

    @commands.command()
    async def guess(self, ctx, *, answer):
        if ctx.author.name not in self.player_score:
            await ctx.send(f"{ctx.author.name} is not a player.")
            return
        if answer == self.now_answer:
            self._add_point(ctx.author.name, 1)
            await ctx.send(f"{ctx.author.name} bingo!")
            # self.sg._next()

    @commands.command()
    async def add(self, ctx, player, point):
        if player in self.player_score:
            self._add_point(player, point)
            await ctx.send(f"{player}: {self.player_score['player']}")

    @commands.command()
    async def setpoint(self, ctx, player, point):
        if player in self.player_score:
            self._set_point(player, point)
            await ctx.send(f"{player}: {self.player_score['player']}")

    @commands.command()
    async def resetpoint(self, ctx):
        self._reset_point()
        await ctx.send(f"Points of all players have reset")

    @commands.command()
    async def join(self, ctx):
        if ctx.author.name in self.player_score:
            await ctx.send(f"{ctx.author.name} is already a player.")
            return
        self.player_score[ctx.author.name] = 0
        await ctx.send(f"{ctx.author.name} has joined.")

    @commands.command()
    async def leave(self, ctx):
        if ctx.author.name not in self.player_score:
            await ctx.send(f"{ctx.author.name} is not a player.")
            return
        del self.player_score[ctx.author.name]
        await ctx.send(f"{ctx.author.name} has left.")
        
    @commands.command()
    async def answer(self, ctx):
        if ctx.author.name not in self.player_score:
            await ctx.send(f"{ctx.author.name} is not a player.")
            return
        await ctx.send(f"The answer is {self.now_answer}")

    @commands.command()
    async def scores(self, ctx):
        if ctx.author.name not in self.player_score:
            await ctx.send(f"{ctx.author.name} is not a player.")
            return
        await ctx.send(f"{self.player_score}")
    