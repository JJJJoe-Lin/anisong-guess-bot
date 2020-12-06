import asyncio
import functools

# import pytube
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
        self.song_info = {}
        self.downloader = youtube_dl.YoutubeDL(ytdl_opts)

    def set_download_task(self):
        self.task = self.loop.create_task(self._download_song())

    async def _download_song(self):
        assert self.info["url"], "no download url"

        # if self.info["url"].find("watch?v") != -1:
        #     self.song_info["id"] = self.info["url"].split("/")[-1].replace("watch?v=", "")
        # else:
        #     self.song_info["id"] = self.info["url"].split("/")[-1]
        
        for _ in range(3):
            try:
                # downloader = await self.loop.run_in_executor(
                # self.thread_pool, functools.partial(pytube.YouTube, self.info["url"]))
                # self.song_info["duration"] = int(downloader.length)
                # self.song_info["path"] = await self.loop.run_in_executor(
                #     self.thread_pool,
                #     functools.partial(downloader.streams.filter(only_audio=True).order_by("abr").last().download,
                #                       output_path="cache", filename=self.song_info["id"])
                #     )
                self.song_info = await self.loop.run_in_executor(self.thread_pool,
                    functools.partial(self.downloader.extract_info, self.info["url"], download=True))
                self.song_info["path"] = self.song_info["id"] + ".opus"
                break
            except Exception as e:
                print(f"Error on download: {str(e)}")
                self.downloader = youtube_dl.YoutubeDL(ytdl_opts)
                await asyncio.sleep(5)
        else:
            print(f"\nError on download: {self.info}\n")
            raise youtube_dl.utils.DownloadError
            # raise pytube.exceptions.PytubeError
        return self.song_info

    
