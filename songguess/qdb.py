import abc
from collections import OrderedDict

from discord.ext import commands
from discord.ext.commands import Group

from .db import DatabaseABC

class CogABCMeta(commands.CogMeta, abc.ABCMeta):
    pass

class QuestionDB(abc.ABC):

    @abc.abstractmethod
    def get_questions(self):
        pass

class SgQDB(commands.Cog, QuestionDB, metaclass=CogABCMeta):
    def __init__(self, bot, config, db: DatabaseABC):
        self.bot = bot
        self.config = config
        self.db = db

        self.theme = config.get("QDB", "theme", fallback="anime_song")
        self.conditions = {}        # conditions format: {<field>: [(<op>, <value>),...]}
        self.cache = OrderedDict()
    
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
            if "singer" in self.conditions:
                def select(item):
                    if item[0] in ["==", "in"]:
                        return False
                    else:
                        return True
                self.conditions["singer"] = list(filter(select, self.conditions["singer"]))
            else:
                self.conditions["singer"] = []
            self.conditions["singer"].append(("==", value))
        elif op.lower() == "include":
            if "singer" in self.conditions:
                def select(item):
                    if item[0] == "==":
                        return False
                    elif item[0] == "in":
                        return True
                self.conditions["singer"] = list(filter(select, self.conditions["singer"]))
                for opv in self.conditions["singer"]:
                    if opv[0] == "in":
                        if len(opv[1]) == 10:
                            await ctx.send("最多只能 include 10 個")
                            return
                        opv[1].append(value)
                        break
                else:
                    self.conditions["singer"].append(("in", [value]))
            else:
                self.conditions["singer"] = []
                self.conditions["singer"].append(("in", [value]))
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
            await ctx.send("format should be \"year {> | >= | == | <= | <} <value>\"")
            return

        if op == "==":
            if "year" in self.conditions:
                def select(item):
                    if item[0] in [">", ">=", "==", "<=", "<"]:
                        return False
                    else:
                        return True
                self.conditions["year"] = list(filter(select, self.conditions["year"]))
            else:
                self.conditions["year"] = []
            self.conditions["year"].append(("==", value))
        elif op in [">", ">="]:
            if "year" in self.conditions:
                def select(item):
                    if item[0] in [">", ">=", "=="]:
                        return False
                    elif item[0] in ["<", "<="]:
                        return True
                self.conditions["year"] = list(filter(select, self.conditions["year"]))
            else:
                self.conditions["year"] = []
            self.conditions["year"].append((op, value))
        elif op in ["<", "<="]:
            if "year" in self.conditions:
                def select(item):
                    if item[0] in ["<", "<=", "=="]:
                        return False
                    elif item[0] in [">", ">="]:
                        return True
                self.conditions["year"] = list(filter(select, self.conditions["year"]))
            else:
                self.conditions["year"] = []
            self.conditions["year"].append((op, value))
        else:
            await ctx.send("format should be \"year {> | >= | == | <= | <} <value>\"")
            return
        await ctx.send(f"condition \"{cond}\" is set")

    @cond.command(name="tags")
    async def set_cond_tags(self, ctx, *, cond: str):
        """
        Format: tags {is | include} <value>
        """
        op, value = cond.split(" ", 1)

        if op.lower() == "is":
            if "tags" in self.conditions:
                def select(item):
                    if item[0] in ["array_contains", "array_contains_any"]:
                        return False
                    else:
                        return True
                self.conditions["tags"] = list(filter(select, self.conditions["tags"]))
            else:
                self.conditions["tags"] = []
            self.conditions["tags"].append(("array_contains", value))
        elif op.lower() == "include":
            if "tags" in self.conditions:
                def select(item):
                    if item[0] == "array_contains":
                        return False
                    elif item[0] == "array_contains_any":
                        return True
                self.conditions["tags"] = list(filter(select, self.conditions["tags"]))
                for opv in self.conditions["tags"]:
                    if opv[0] == "array_contains_any":
                        if len(opv[1]) == 10:
                            await ctx.send("最多只能 include 10 個")
                            return
                        opv[1].append(value)
                        break
                else:
                    self.conditions["tags"].append(("array_contains_any", [value]))
            else:
                self.conditions["tags"] = []
                self.conditions["tags"].append(("array_contains_any", [value]))
        else:
            await ctx.send("format should be \"tags {is | include} <value>\"")
            return
        await ctx.send(f"condition \"{cond}\" is set")

    @cond.command(name="reset")
    async def reset_cond(self, ctx):
        self.conditions = {}
        await ctx.send("condition has been reset")

    @cond.command(name="show")
    async def show_cond(self, ctx):
        msg = f"The condition:\n"
        for field, ops in self.conditions.items():
            for op in ops:
                msg += f"{field} {op[0]} {op[1]}\n"
        await ctx.send(msg)

    def _send_get_query(self):
        conflict_conds = []     # 'range_cond on different field', 'in', 'array-contains-any'
        fix_conds = []
        result_sets = []

        for field, ops in self.conditions.items():
            range_conds = []      # '<', '<=', '>=', '>', '!='
            for op in ops:
                if op[0] in ["<", "<=", ">=", ">", "!="]:
                    range_conds.append((field, op[0], op[1]))
                elif op[0] in ["in", "array_contains_any"]:
                    conflict_conds.append((field, op[0], op[1]))
                else:
                    fix_conds.append((field, op[0], op[1]))
            conflict_conds.append(range_conds)

        if not conflict_conds:
            query = fix_conds
            result_sets.append(set(self.db.exec_get(self.theme, query)))
        else:
            for cc in conflict_conds:
                if isinstance(cc, list):
                    query = cc + fix_conds
                else:
                    query = [cc] + fix_conds
                result_sets.append(set(self.db.exec_get(self.theme, query)))

        if len(result_sets) == 1:
            return list(result_sets[0])

        return list(set.intersection(*result_sets))

    def get_questions(self):
        if str(self.conditions) not in self.cache:
            results = self._send_get_query()
            dict_result = [doc.to_dict() for doc in results]
            if len(self.cache) == 5:
                self.cache.popitem(last=False)
            self.cache[str(self.conditions)] = dict_result
        return self.cache[str(self.conditions)]

class AnimeSgQDB(SgQDB):
    cond = SgQDB.cond

    def __init__(self, bot, config, db: DatabaseABC):
        super().__init__(bot, config, db)

    @cond.command(name="anime")
    async def set_cond_anime(self, ctx, *, cond: str):
        """
        Format: anime {is | include} <value>
        """
        op, value = cond.split(" ", 1)

        if op.lower() == "is":
            if "anime" in self.conditions:
                def select(item):
                    if item[0] in ["==", "in"]:
                        return False
                    else:
                        return True
                self.conditions["anime"] = list(filter(select, self.conditions["anime"]))
            else:
                self.conditions["anime"] = []
            self.conditions["anime"].append(("==", value))
        elif op.lower() == "include":
            if "anime" in self.conditions:
                def select(item):
                    if item[0] == "==":
                        return False
                    elif item[0] == "in":
                        return True
                self.conditions["anime"] = list(filter(select, self.conditions["anime"]))
                for opv in self.conditions["anime"]:
                    if opv[0] == "in":
                        if len(opv[1]) == 10:
                            await ctx.send("最多只能 include 10 個")
                            return
                        opv[1].append(value)
                        break
                else:
                    self.conditions["anime"].append(("in", [value]))
            else:
                self.conditions["anime"] = []
                self.conditions["anime"].append(("in", [value]))
        else:
            await ctx.send("format should be \"anime {is | include} <value>\"")
            return
        await ctx.send(f"condition \"{cond}\" is set")

    @cond.command(name="type")
    async def set_cond_type(self, ctx, *, cond: str):
        """
        Format: type {is | include} <value>
        """
        op, value = cond.split(" ", 1)

        if op.lower() == "is":
            if "type" in self.conditions:
                def select(item):
                    if item[0] in ["==", "in"]:
                        return False
                    else:
                        return True
                self.conditions["type"] = list(filter(select, self.conditions["type"]))
            else:
                self.conditions["type"] = []
            self.conditions["type"].append(("==", value))
        elif op.lower() == "include":
            if "type" in self.conditions:
                def select(item):
                    if item[0] == "==":
                        return False
                    elif item[0] == "in":
                        return True
                self.conditions["type"] = list(filter(select, self.conditions["type"]))
                for opv in self.conditions["type"]:
                    if opv[0] == "in":
                        if len(opv[1]) == 10:
                            await ctx.send("最多只能 include 10 個")
                            return
                        opv[1].append(value)
                        break
                else:
                    self.conditions["type"].append(("in", [value]))
            else:
                self.conditions["type"] = []
                self.conditions["type"].append(("in", [value]))
        else:
            await ctx.send("format should be \"type {is | include} <value>\"")
            return
        await ctx.send(f"condition \"{cond}\" is set")
