import discord
from discord.ext import commands

from .question import Question
from .sql import FirestoreSGSQL

class QuestionQueue(object):
    def __init__(self, sql: FirestoreSGSQL):
        self.sql = sql
        self.qlist = []

    def prepare(self, loop):
        entries = self.sql.get_result_list()
        for entry in entries:
            assert entry["url"], "no download url"
            q = Question(entry, loop)
            self.qlist.append(q)

        # TODO: 下載排程
        for q in self.qlist:
            q.set_download_task()

    async def get_question(self):
        if not self.qlist:
            return None
        q = self.qlist.pop()
        await q.task
        return q