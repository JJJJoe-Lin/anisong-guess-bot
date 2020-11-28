import random
from concurrent.futures import ThreadPoolExecutor

from .question import Question
from .qdb import QuestionDB

class QuestionQueue(object):
    def __init__(self, qdb: QuestionDB, event_loop, cache_size: int, thread_num: int):
        self.qdb = qdb
        self.loop = event_loop
        self.cache_size = cache_size
        self.thread_pool = ThreadPoolExecutor(max_workers=thread_num)

        self.qlist = []
        self.number = 0

    def _download_scheduling(self):
        size = self.cache_size if len(self.qlist) > self.cache_size else len(self.qlist)
        for i in range(size):
            if self.qlist[i].task is None:
                self.qlist[i].set_download_task()

    def prepare(self, amount, is_anime_dup=False):
        # reset queue
        self.qlist = []
        self.number = 0
        
        entries = self.qdb.get_questions()
        if not entries:
            return 0

        if is_anime_dup:
            if len(entries) > amount:
                entries = random.sample(entries, amount)
            else:
                random.shuffle(entries)
            for entry in entries:
                assert entry["url"], "no download url"
                q = Question(entry, self.loop, self.thread_pool)
                self.qlist.append(q)
        else:
            while True:
                if len(self.qlist) == amount:
                    break
                if not entries:
                    break
                entry = random.choice(entries)
                entries.remove(entry)
                if entry["anime"] in [q.info["anime"] for q in self.qlist]:
                    continue
                q = Question(entry, self.loop, self.thread_pool)
                self.qlist.append(q)

        self._download_scheduling()
        return len(self.qlist)

    async def get_question(self):
        if not self.qlist:
            return None
        while self.qlist:
            try:
                # ensure download task been scheduled
                self._download_scheduling()
                q = self.qlist.pop(0)
                self.number += 1
                await q.task
            except Exception:
                # print(f"The song {q.info['name']} got pass")
                pass
            else:
                return q
        return None