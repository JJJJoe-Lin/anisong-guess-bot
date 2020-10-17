import discord
from discord.ext import commands

from .question import Question

class QuestionQueue(object):
    def __init__(self):
        self.qlist = []

    def prepare(self, qdb, loop):
        entries = qdb.get_data_list()
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