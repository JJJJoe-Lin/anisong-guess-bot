import random

from .question import Question
from .qdb import SgQDB

class QuestionQueue(object):
    def __init__(self, qdb: SgQDB):
        self.qdb = qdb
        self.qlist = []

    def prepare(self, loop, amount):
        entries = self.qdb.get_result()

        if len(entries) > amount:
            entries = random.sample(entries, amount)
        else:
            random.shuffle(entries)

        for entry in entries:
            assert entry["url"], "no download url"
            q = Question(entry, loop)
            self.qlist.append(q)

        # TODO: 下載排程
        for q in self.qlist:
            print(q.info["name"])
            q.set_download_task()

    async def get_question(self):
        if not self.qlist:
            return None
        q = self.qlist.pop()
        await q.task
        return q