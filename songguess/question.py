import asyncio
import functools

import pytube

class Question(object):
    def __init__(self, info, loop, thread_pool):
        self.info = info
        self.loop = loop
        self.task = None
        self.thread_pool = thread_pool

    def set_download_task(self):
        self.task = self.loop.create_task(self._download_song())

    async def _download_song(self):
        assert self.info["url"], "no download url"

        ie = {}
        if self.info["url"].find("watch?v") != -1:
            ie["id"] = self.info["url"].split("/")[-1].replace("watch?v=", "")
        else:
            ie["id"] = self.info["url"].split("/")[-1]
        
        for _ in range(5):
            try:
                downloader = await self.loop.run_in_executor(self.thread_pool,
                                functools.partial(pytube.YouTube, self.info["url"]))
                ie["duration"] = int(downloader.length)
                ie["path"] = await self.loop.run_in_executor(self.thread_pool,
                                functools.partial(downloader.streams.filter(only_audio=True).order_by("abr").last().download, output_path="cache", filename=ie["id"]))
                break
            except Exception as e:
                print(f"Error on download: {str(e)}")
                await asyncio.sleep(5)
        else:
            print(f"\nError on download: {self.info}\n")
            raise pytube.exceptions.PytubeError
        return ie

    