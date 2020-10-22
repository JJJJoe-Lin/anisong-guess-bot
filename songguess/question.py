import asyncio
import functools

import youtube_dl

ytdl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'./cache/%(id)s.%(ext)s',
        'quiet': True,
        'nocheckcertificate': True,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
        }]
}

class Question(object):
    def __init__(self, info, loop, thread_pool):
        self.info = info
        self.loop = loop
        self.task = None
        self.thread_pool = thread_pool
        self.downloader = youtube_dl.YoutubeDL(ytdl_opts)
        pass

    def set_download_task(self):
        self.task = self.loop.create_task(self._download_song())

    async def _download_song(self):
        assert self.info["url"], "no download url"
        for _ in range(5):
            try:
                ie = await self.loop.run_in_executor(self.thread_pool,
                        functools.partial(self.downloader.extract_info, self.info["url"], download=True))
                break
            except Exception as e:
                print(f"Error on download: {str(e)}")
        else:
            raise youtube_dl.utils.DownloadError
        return ie

    