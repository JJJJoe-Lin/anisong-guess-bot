import os
import asyncio
from collections import deque

import discord
from discord.ext import commands

class MusicPlayer(object):
    def __init__(self, cache: str):
        self.voiceClient = None
        self.is_running = False
        self.now_playing = {"file": "", "start": 0, "length": 0}
        self.cacheFolder = cache

    async def start(self, channel: discord.VoiceChannel):
        self.voiceClient = await channel.connect()
        self.is_running = True

    async def close(self):
        if self.voiceClient.is_connected():
            await self.voiceClient.disconnect()
            self.is_running = False

    async def play(self, file: str, start=0, length=0):
        path = os.path.join(self.cacheFolder, file)
        assert self.is_running, "Player is not running"
        assert os.path.isfile(path), "Path is not exist"

        bfOpt = "-nostdin"
        if start != 0:
            bfOpt = bfOpt + " -ss " + time_format_ffmpeg(start)
        if length != 0:
            bfOpt = bfOpt + " -t " + time_format_ffmpeg(length)

        # self.now_playing = discord.FFmpegPCMAudio(path, before_options=bfOpt, options="-vn")
        source = await discord.FFmpegOpusAudio.from_probe(path, before_options=bfOpt, options="-vn")

        if self.now_playing["file"] and file != self.now_playing["file"]:
            await self.stop_and_delete()
        else:
            self.stop()
        self.voiceClient.play(source)

        self.now_playing["file"] = file
        self.now_playing["start"] = start
        self.now_playing["length"] = length

    def stop(self):
        assert self.is_running, "Player is not running"
        if self.voiceClient.is_playing():
            self.voiceClient.stop()

    async def _delete_file(self, path):
        try:
            os.unlink(path)
        except Exception as e:
            print(f"Error trying to delete {path}: {str(e)}")

    async def stop_and_delete(self):
        assert self.is_running, "Player is not running"
        self.stop()
        await self._delete_file(os.path.join(self.cacheFolder, self.now_playing["file"]))

    async def replay(self):
        assert self.is_running, "Player is not running"
        await self.play(**self.now_playing)


def time_format_ffmpeg(s: int):
    sec = int(s % 60)
    mins = int((s / 60) % 60)
    hours = int(s / 3600)
    return f"{hours:02d}:{mins:02d}:{sec:02d}"


    