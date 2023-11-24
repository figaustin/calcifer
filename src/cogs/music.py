import discord
from discord.ext import commands
from discord import app_commands
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
import asyncio


FFMPEG_BEFORE_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTIONS = "-vn"

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.playing = False
        self.paused = False

        self.queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio/best', 'quiet' : 'true'}

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
            print("found next")
            self.playing = True

            #get the first url
            m_url = self.queue[0]['source']

            #remove the first element as you are currently playing it
            self.queue.pop(0)
            loop = asyncio.get_event_loop()
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                data = await loop.run_in_executor(None, lambda: ydl.extract_info(m_url, download=False))
                song = data['url']
                self.vc.play(discord.FFmpegPCMAudio(song, before_options=FFMPEG_BEFORE_OPTIONS, options=FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
        else:
            print("didnt find next")
            self.playing = False
            # await self.vc.disconnect()

    # infinite loop checking 
    async def play_music(self, interaction):
        if len(self.queue) > 0:
            self.playing = True

            m_url = self.queue[0]['source']
            #try to connect to voice channel if you are not already connected
            if self.vc == None or not self.vc.is_connected():
                self.vc = await interaction.user.voice.channel.connect()
                #in case we fail to connect
                if self.vc == None :
                    await interaction.response.send_message("🔥 Could not connect to the voice channel 🔥")
                    return
            #remove the first element as you are currently playing it
            self.queue.pop(0)

            loop = asyncio.get_event_loop()
            with YoutubeDL(self.YDL_OPTIONS) as ydl: 
                data = await loop.run_in_executor(None, lambda: ydl.extract_info(m_url, download=False))
                song = data['url']
                self.vc.play(discord.FFmpegPCMAudio(source=song, before_options=FFMPEG_BEFORE_OPTIONS, options=FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
            
        else:
            self.playing = False

    @app_commands.command(name="play", description="Search for a song!")
    @app_commands.describe(query="query")
    async def play(self, interaction: discord.Interaction, query: str):

        try:
            voice_channel = interaction.user.voice.channel
        except:
            await interaction.response.send_message("🔥 You need to connect to a voice channel first! 🔥")
            return
        
        if self.paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)

            if type(song) == type(True):
                await interaction.response.send_message("🔥 Could not play the song, because of incorrect format, try another keyword. This could be due to playlist or a livestream format. 🔥")
            else:
                await interaction.response.send_message(f"🔥 **'{song['title']}'** added to the queue! 🔥")  

                self.queue.append(song)
                if self.playing == False:
                    await self.play_music(interaction)


    @app_commands.command(name="pause", description="Pauses the current song being played")
    async def pause(self, interaction: discord.Interaction):
        if self.playing:
            self.playing = False
            self.paused = True
            self.vc.pause()
            await interaction.response.send_message(f"🔥 Paused current song! 🔥")
        elif self.paused:
            self.paused = False
            self.playing = True
            self.vc.resume()
            await interaction.response.send_message(f"🔥 Unpaused current song! 🔥")

    @app_commands.command(name="ping", description="Ping the server!")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Pong!")

    @app_commands.command(name="skip", description="Skips to the next song in the queue")
    async def skip(self, interaction: discord.Interaction):
        if self.vc != None and self.vc:
            self.vc.stop()

            await interaction.response.send_message("🔥 Skipped to the next song! 🔥")

    @app_commands.command(name="queue", description="Shows the songs in the music queue")
    async def show_queue(self, interaction: discord.Interaction):
        queue_str = ""
        for x in range(0, len(self.queue)):
            queue_str += f"{x + 1}. **" + self.queue[x]['title'] +  "** \n"

        if queue_str != "":
            await interaction.response.send_message(f"🎶🔥 **Music Queue** 🔥🎶" + "\n" + "--------------------------------------------\n" + queue_str)
        else:
            await interaction.response.send_message(f"🎶🔥 The music queue is empty! Add songs with **/play!** 🔥🎶")
    
    @app_commands.command(name="stop", description="Clears queue and disconnects Calcifer")
    async def stop(self, interaction: discord.Interaction):
        if interaction.user.voice.channel == None:
            await interaction.response.send_message("🔥 You need to connect to a voice channel first! 🔥")

        if self.vc != None and self.vc:
            self.queue = []
            self.vc.stop()
            await self.vc.disconnect()
            await interaction.response.send_message("🔥 Stopped playing music and disconnected! 🔥")