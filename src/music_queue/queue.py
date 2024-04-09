import discord
import discord.ext.commands
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
import asyncio


FFMPEG_BEFORE_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTIONS = "-vn"

queues = []

class Song():

    def __init__(self, song_type, title, duration, thumbnail, url, member: discord.Member):
        self.song_type = song_type
        self.title = title
        self.duration = duration
        self.thumbnail = thumbnail
        self.url = url
        self.member = member

class Playlist():
    def __init__(self, count, title):
        self.count = count
        self. title = title

class Queue():

    def __init__(self, client, guild_id):
        self.client: discord.Client = client

        self.playing = False
        self.paused = False

        self.queue: list[Song] = []
        self.now_playing: Song = None

        self.YDL_OPTIONS = {'format': 'bestaudio/best', 'quiet' : 'true'}

        self.vc = None
        self.guild_id = guild_id

    async def search_yt(self, query, interaction: discord.Interaction) -> Song:
        if "list=" in query:
            raise PlaylistError("The url provided was a playlist, use a keyword, url without a playlist or use the playlist function")
        if "youtube" in query:
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                info = ydl.extract_info(query, download=False)
                song = Song("youtube", info["title"], info["duration_string"], info["thumbnail"], info["webpage_url"], interaction.user)
        else:
            search = VideosSearch(query, limit=5)
            try:
                result = search.result()["result"][0]
            except IndexError:
                raise QueueError("Search query yielded no results, try again with a different keyword!")
            song = Song("youtube", result["title"], result["duration"], result["thumbnails"][0]["url"],
                        "https://www.youtube.com/watch?v=" + result["id"], interaction.user)
        return song
            
    async def add_to_queue(self, interaction: discord.Interaction, query: str) -> list[Song]:

        song = await self.search_yt(query, interaction)
        self.queue.append(song)

        if not self.playing:
            await self.play(interaction)
        return song
    
    async def play(self, interaction: discord.Interaction):

        if len(self.queue) > 0:

            url = self.queue[0].url

            if self.vc == None or not self.vc.is_connected():
                self.vc = await interaction.user.voice.channel.connect()

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
                                                options=FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play(interaction), self.client.loop))
        else:
            self.playing=False
            await self.stop()
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
    #             self.vc.play(discord.FFmpegPCMAudio(song, before_options=FFMPEG_BEFORE_OPTIONS, options=FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.client.loop))
    #     else:
    #         self.playing = False
    #         await self.vc.disconnect()

    async def pause(self):
        if self.playing and not self.paused:
            self.playing = False
            self.paused = True
            try:
                self.vc.pause()
            except Exception as e:
                raise QueueError(f"Queue was not able to paused: {e}")
            return True
    
    async def resume(self):
        if self.paused:
            self.playing = True
            self.paused = False
            try:
                self.vc.resume()
            except Exception as e:
                raise PauseResumeError(f"Queue could not be resumed: {e}")
            return True
        
    async def skip(self):
        if self.vc != None and self.vc:
            try:
                #Voice channel Stop function is used here to easily use the client/bot's loop(If the current stream is stopped/finished, the next song/stream will play)
                self.vc.stop()
            except Exception:
                raise QueueError("Queue could not be skipped!")
        
            return True
            
    async def stop(self):
        if self.vc != None and self.vc:
            self.queue = []
            for x in range(len(queues)):
                if queues[x].guild_id== self.guild_id:
                    queues.pop(x)
            try:
                self.vc.stop()
            except Exception:
                raise QueueError("Queue could not be stopped!")
            await self.vc.disconnect()
            await remove_from_queue_list(self)

    async def playlist(self, interaction: discord.Interaction, url: str) -> Playlist:

        if "list=" not in url:
            raise PlaylistError("Provided url was not a playlist")
        
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            entries = info["entries"]
            playlist = Playlist(info["playlist_count"], info["title"])

            for entry in entries:
                song = Song("youtube", entry["title"], entry["duration_string"],
                            entry["thumbnail"], entry["webpage_url"])
                self.queue.append(song)
        
        if not self.playing:
            try:
                await self.play(interaction)
            except Exception:
                raise QueueError("Could not play the queue")
        return playlist

    async def get_queue(self) -> list[Song]:
        return self.queue
    
    async def get_now_playing(self) -> Song:
        return self.now_playing
    
            
class QueueError(Exception):
    """Basic class for errors that have to do with the client's music queue"""
    def __init__(self, message=None):
        self.message = message
        super().__init__(message)

class PauseResumeError(Exception):
    """For throwing any errors with pausing queue"""
    def __init__(self, message=None):
        self.message = message
        super().__init__(message)

class PlaylistError(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(message)

async def find_or_add_queue(client, guild_id):
    if len(queues) == 0:
        new_queue = Queue(client, guild_id)
        queues.append(new_queue)
        return new_queue  
    else:
        for q in queues:
            if q.guild_id == guild_id:
                return q

        new_queue = Queue(client, guild_id)
        queues.append(new_queue)
        return new_queue
    
async def remove_from_queue_list(queue: Queue):

    for x in range(len(queues)):
            if queues[x].guild_id == queue.guild_id:
                queues.pop(x)