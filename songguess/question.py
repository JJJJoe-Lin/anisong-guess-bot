import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor

import discord
from discord.ext import commands
import youtube_dl

ytdl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'./cache/%(id)s.%(ext)s',
        'quiet': True,
        'nocheckcertificate': True,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]
}

class Question(object):
    def __init__(self, info, loop):
        self.info = info
        self.loop = loop
        self.task = None
        self.is_ready = False
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        self.downloader = youtube_dl.YoutubeDL(ytdl_opts)
        pass

    def set_download_task(self):
        assert not self.is_ready and not self.task, "file has downloaded"
        self.task = self.loop.create_task(self._download_song())

    async def _download_song(self):
        assert self.info["url"], "no download url"
        ie = await self.loop.run_in_executor(self.thread_pool,
                functools.partial(self.downloader.extract_info, self.info["url"], download=True))
        self.is_ready = True
        return ie["id"]

    