import discord
import discord.ext.commands
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
import asyncio


FFMPEG_BEFORE_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTIONS = "-vn"

queues = []

class Song():

    def __init__(self, song_type, title, length, thumbnail, url):
        self.song_type = song_type
        self.title = title
        self.length = length
        self.thumbnail = thumbnail
        self.url = url


class Queue():

    def __init__(self, bot, guild_id):
        self.bot: discord.Bot = bot

        self.playing = False
        self.paused = False

        self.queue: list[Song] = []
        self.now_playing: Song = None

        self.YDL_OPTIONS = {'format': 'bestaudio/best', 'quiet' : 'true'}

        self.vc = None
        self.guild_id = guild_id

    async def search_yt(self, query) -> Song:
        if "list=" in query:
            raise QueueError("The provided url is a playlist!")
        if "youtube" in query:
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                info = ydl.extract_info(query, download=False)
                song = Song("youtube", info["title"], info["duration_string"], info["thumbnail"], info["webpage_url"] )
        else:
            search = VideosSearch(query, limit=5)
            try:
                result = search.result()["result"][0]
            except IndexError:
                raise QueueError("Search query yielded no results, try again with a different keyword!")
            song = Song("youtube", result["title"], result["duration"], result["thumbnails"][0]["url"],
                        "https://www.youtube.com/watch?v=" + result["id"])
        return song
            
    async def add_to_queue(self, ctx, query: str) -> list[Song]:

        song = await self.search_yt(query)
        self.queue.append(song)

        if not self.playing:
            await self.play(ctx)
        return song
    
    async def play(self, ctx):

        if len(self.queue) > 0:

            url = self.queue[0].url

            if self.vc == None or not self.vc.is_connected():
                self.vc = await ctx.author.voice.channel.connect()

                #in case we fail to connect
                if self.vc == None:
                    return False
            self.playing = True
            self.now_playing = self.queue[0]
            self.queue.pop(0)

            loop = asyncio.get_event_loop()
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                song = data['url']
                self.vc.play(discord.FFmpegPCMAudio(source=song, before_options=FFMPEG_BEFORE_OPTIONS,
                                                options=FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play(ctx), self.bot.loop))
        else:
            self.playing=False
            return False

    #Keeping this here just incase (Now commented out because it is literally the same as the regular play function above???)
    # async def play_next(self):
    #     if len(self.queue) > 0:
    #         self.playing = True

    #         url = self.queue[0].url

    #         self.queue.pop(0)

    #         loop = asyncio.get_event_loop()
    #         with YoutubeDL(self.YDL_OPTIONS) as ydl:
    #             data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
    #             song = data['url']
    #             self.vc.play(discord.FFmpegPCMAudio(song, before_options=FFMPEG_BEFORE_OPTIONS, options=FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
    #     else:
    #         self.playing = False
    #         await self.vc.disconnect()

    async def pause(self):
        if self.playing:
            self.playing = False
            self.paused = True
            try:
                self.vc.pause()
            except Exception:
                raise QueueError("Queue was not able to paused!")
            return True
        elif self.paused:
            self.paused = False
            self.playing = True
            try:
                self.vc.resume()
            except Exception:
                raise QueueError("Queue was not able to resumed!")
            return True
        
    async def skip(self):
        if self.vc != None and self.vc:
            try:
                self.vc.stop()
            except Exception:
                raise QueueError("Queue could not be skipped!")
        
            return True
            
    async def get_queue(self) -> list[Song]:
        return self.queue
    
    async def stop(self):
        if self.vc != None and self.vc:
            self.queue = []
            for x in range(len(queues)):
                if queues[x] == self:
                    queues.pop(x)
            try:
                self.vc.stop()
            except Exception:
                raise QueueError("Queue could not be stopped!")
            await self.vc.disconnect()
            
class QueueError(Exception):
    """Basic class for errors that have to do with the bot's music queue"""
    def __init__(self, message=None):
        self.message = message
        super().__init__(message)

async def find_or_add_queue(bot, guild_id):
    if len(queues) == 0:
        new_queue = Queue(bot, guild_id)
        queues.append(new_queue)
        return new_queue  
    else:
        for q in queues:
            if q.guild_id == guild_id:
                return q

        new_queue = Queue(bot, guild_id)
        queues.append(new_queue)
        return new_queue