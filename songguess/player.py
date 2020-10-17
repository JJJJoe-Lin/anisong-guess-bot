import os

import discord
from discord.ext import commands

class MusicPlayer(object):
    def __init__(self, cache: str):
        self.voiceClient = None
        self.isRunning = False
        self.cacheFolder = cache

    async def start(self, channel: discord.VoiceChannel):
        self.voiceClient = await channel.connect()
        self.isRunning = True

    async def close(self):
        if self.voiceClient.is_connected():
            await self.voiceClient.disconnect()
            self.isRunning = False

    async def play(self, file: str, start=0, length=0):
        # TODO: 能匹配不同副檔名
        path = os.path.join(self.cacheFolder, file)
        if os.path.isfile(path):
            bfOpt = "-nostdin"
            if start != 0:
                bfOpt = bfOpt + " -ss " + timeFormat_ffmpeg(start)
            if length != 0:
                bfOpt = bfOpt + " -t " + timeFormat_ffmpeg(length)

            source = discord.FFmpegPCMAudio(path, before_options=bfOpt, options="-vn")
            # source = await discord.FFmpegOpusAudio.from_probe(path, before_options=bfOpt, options="-vn")

            self.voiceClient.play(source)
        
        # TODO: 拋出例外

    async def stop(self):
        if self.voiceClient.is_playing():
            self.voiceClient.stop()
            

def timeFormat_ffmpeg(s: int):
    sec = s % 60
    mins = (s / 60) % 60
    hours = s / 3600
    return f"{hours:02d}:{mins:02d}:{sec:02d}"


    