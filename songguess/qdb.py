import abc

from discord.ext import commands

from .db import DatabaseABC

class CogABCMeta(commands.CogMeta, abc.ABCMeta):
    pass

class QuestionDB(abc.ABC):

    @abc.abstractmethod
    def get_result(self):
        pass

class SgQDB(commands.Cog, QuestionDB, metaclass=CogABCMeta):
    def __init__(self, bot, config, db: DatabaseABC):
        self.bot = bot
        self.config = config
        self.db = db

        # condition config
        self.cond_singer = []
        self.cond_year = []
        self.cond_attr = []

    """ Condition Setting """

    @commands.group()
    async def cond(self, ctx):
        """
        Format: <command_prefix>cond <field> <op> <value>
        """
        pass

    @cond.command(name="singer")
    async def set_cond_singer(self, ctx, *, cond: str):
        """
        Format: singer {is | include} <value>
        """
        op, value = cond.split(" ", 1)
        if op.lower() == "is":
            self.cond_singer = [value]
        elif op.lower() == "include":
            self.cond_singer.append(value)
        else:
            await ctx.send("format should be \"singer {is | include} <value>\"")
            return
        await ctx.send(f"condition \"{cond}\" is set")

    @cond.command(name="year")
    async def set_cond_year(self, ctx, *, cond: str):
        """
        Format: year {> | >= | == | =< | <} <value>
        """
        op = cond.split(" ", 1)[0]
        try:
            value = int(cond.split(" ", 1)[1])
        except ValueError:
            await ctx.send("format should be \"year {> | >= | == | =< | <} <value>\"")
            return

        if op in [">", ">=", "==", "=<", "<"]:
            self.cond_year.append([op, value])
        else:
            await ctx.send("format should be \"year {> | >= | == | =< | <} <value>\"")
            return
        await ctx.send(f"condition \"{cond}\" is set")

    @cond.command(name="attr")
    async def set_cond_attr(self, ctx, *, cond: str):
        """
        Format: attr {is | include} <value>
        """
        op, value = cond.split(" ", 1)
        if op.lower() == "is":
            del self.cond_attr
            self.cond_attr = [value]
        elif op.lower() == "include":
            self.cond_attr.append(value)
        else:
            await ctx.send("format should be \"attr {is | include} <value>\"")
            return
        await ctx.send(f"condition \"{cond}\" is set")

    @cond.command(name="reset")
    async def reset_cond(self, ctx):
        self.cond_singer = []
        self.cond_year = []
        self.cond_attr = []
        await ctx.send("condition has been reset")

    @cond.command(name="show")
    async def show_cond(self, ctx):
        msg = f"The condition:\n"
        if self.cond_singer:
            msg += f"singer in {self.cond_singer}\n"
        for cond in self.cond_year:
            msg += f"year {cond[0]} {cond[1]}\n"
        if self.cond_attr:
            msg += f"attr in {self.cond_attr}\n"
        await ctx.send(msg)

    def _send_get_ques_query(self):
        ref = None
        if self.cond_singer:
            ref = self.db.exec_query(["singer", "in", self.cond_singer], ref)
        if self.cond_year:
            for cond in self.cond_year:
                ref = self.db.exec_query(["year", cond[0], cond[1]], ref)
        if self.cond_attr:
            ref = self.db.exec_query(["attr", "array_contains_any", self.cond_attr], ref)
        return self.db.get_results(ref)

    def get_result(self):
        return self._send_get_ques_query()