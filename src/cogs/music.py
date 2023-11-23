import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
import asyncio


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.playing = False
        self.paused = False

        self.queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio/best'}
        self.FFMPEG_OPTIONS = {
            'options': '-vn'}

        self.vc = None

    def search_yt(self, item):
        if item.startswith("https://"):
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                info = ydl.extract_info(item, download=False)
                return{'source':item, 'title':info['title']}
        search = VideosSearch(item, limit=5)
        return{'source':search.result()["result"][0]["link"], 'title':search.result()["result"][0]["title"]}
    
    async def play_next(self):
        if len(self.queue) > 0:
            self.playing = True

            #get the first url
            m_url = self.queue[0]['source']

            #remove the first element as you are currently playing it
            self.queue.pop(0)
            loop = asyncio.get_event_loop()
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                data = await loop.run_in_executor(None, lambda: ydl.extract_info(m_url, download=False))
                song = data['url']
                self.vc.play(discord.FFmpegPCMAudio(song, **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
        else:
            self.playing = False

    # infinite loop checking 
    async def play_music(self, ctx):
        if len(self.queue) > 0:
            self.playing = True

            m_url = self.queue[0]['source']
            #try to connect to voice channel if you are not already connected
            if self.vc == None or not self.vc.is_connected():
                self.vc = await ctx.author.voice.channel.connect()
                #in case we fail to connect
                if self.vc == None :
                    await ctx.send("🔥 Could not connect to the voice channel 🔥")
                    return
            #remove the first element as you are currently playing it
            self.queue.pop(0)

            loop = asyncio.get_event_loop()
            with YoutubeDL(self.YDL_OPTIONS) as ydl: 
                data = await loop.run_in_executor(None, lambda: ydl.extract_info(m_url, download=False))
                song = data['url']
                self.vc.play(discord.FFmpegPCMAudio(source=song, options=self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
            
        else:
            self.playing = False

    @commands.command(name="play", aliases=["p","playing"], help="Plays a selected song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)

        try:
            voice_channel = ctx.author.voice.channel
        except:
            await ctx.send("🔥 You need to connect to a voice channel first! 🔥")
            return
        
        if self.paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)

            if type(song) == type(True):
                await ctx.send("🔥 Could not play the song, because of incorrect format, try another keyword. This could be due to playlist or a livestream format. 🔥")
            else:
                if self.playing:
                    await ctx.send(f"🔥 #{len(self.queue)+2} -'{song['title']}' added to the queue! 🔥")  
                else:
                    await ctx.send(f"🔥 '{song['title']}'** added to the queue! 🔥")  

                self.queue.append(song)
                if self.playing == False:
                    await self.play_music(ctx)


    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.playing = False
            self.paused = True
            self.vc.pause()
        elif self.is_paused:
            self.paused = False
            self.playing = True
            self.vc.resume()