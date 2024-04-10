import os
import discord
from discord import app_commands
import discord.ext.commands
from dotenv import load_dotenv
import discord.ext
from music_queue.queue import Queue, find_or_add_queue, QueueError, PauseResumeError, PlaylistError
from embeds import CalciferMusicEmbed
from music_queue.session import MusicSession

load_dotenv()
token = str(os.getenv("TOKEN"))

intents = discord.Intents.default()
intents.message_content = True

class Calcifer(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)
        self.sessions: list[MusicSession] = []

    async def setup_hook(self):
        await self.tree.sync()

    async def get_music_session(self, interaction):
        found = [x for x in self.sessions if x.guild_id == interaction.guild_id]
        if len(found) == 0 or found == None:
            return None
        else:
            return found[0]

calcifer = Calcifer(intents=intents)

@calcifer.event
async def on_ready():
    print(f"Calcifer logged in and ready!")


@calcifer.tree.command(name="ping", description="Ping!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@calcifer.tree.command(name="play", description="Play a song!")
@app_commands.describe(query="query")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    try:
        voice_channel = interaction.user.voice.channel
    except:
        await interaction.response.send_message("🔥 You need to connect to a voice channel first! 🔥")
        return False
    
    # if queue.paused:
    #     #the pause function is also for resuming
    #     await queue.pause()
    # else:

    music_session = await calcifer.get_music_session(interaction)

    if music_session == None:
        music_session = MusicSession(calcifer, interaction.guild.id, interaction)
        calcifer.sessions.append(music_session)

    try:

        queue: Queue = music_session.queue
        song = await queue.add_to_queue(interaction, query)
        text_channel = interaction.channel
        await interaction.followup.send(f"🔥 **'{song.title}'** was added to the queue! 🔥")
        resend = await music_session.embed.send_embed(text_channel)

    except QueueError:
        await interaction.followup.send("🔥 Search yielded no results, please try another keyword! 🔥")
    except PlaylistError:
        await interaction.followup.send("🔥 URL provided was a playlist, please use **/playlist** command for playlists! 🔥")

@calcifer.tree.command(name="pause", description="Pause the current song in queue! Or resume song if it is paused!")
async def pause(interaction: discord.Interaction):
    try:
        music_session = await calcifer.get_music_session(interaction)
        queue: Queue = music_session.queue
        await queue.pause()
        if queue.paused:
            await interaction.response.send_message(f"🔥 Paused the queue! 🔥")
    except QueueError:
        await interaction.response.send_message(f"🔥 Something went wrong! Could not pause the queue! 🔥")

@calcifer.tree.command(name="resume", description="Resume the current song if it is paused!")
async def resume(interaction: discord.Interaction):
    try:
        music_session = await calcifer.get_music_session(interaction)
        queue: Queue = music_session.queue
        await queue.resume()
        await interaction.response.send_message(f"🔥 Resumed the queue! 🔥")
    except PauseResumeError:
        await interaction.response.send_message("🔥 Something went wrong! Could not resume the queue! 🔥")

@calcifer.tree.command(name="skip", description="Skip the current song!")
async def skip(interaction: discord.Interaction):
    try:
        music_session = await calcifer.get_music_session(interaction)
        queue: Queue = music_session.queue
        if len(queue.songs) > 0:
            await queue.skip()
            resend = await music_session.embed.send_embed(interaction.channel)
            await interaction.response.send_message(f"🔥 Skipped to the next song in queue! 🔥")
        else:
            await queue.stop()
            await interaction.response.send_message(f"🔥 Queue was empty! Now disconnecting... 🔥")
    except QueueError:
        await interaction.response.send_message(f"🔥 Something went wrong! Could not skip to next song! 🔥")

@calcifer.tree.command(name="queue", description="Display all the songs currently in the queue!")
async def queue(interaction: discord.Interaction):
    music_session = await calcifer.get_music_session(interaction)
    queue: Queue = music_session.queue
    # songs = await queue.get_queue()
    # now_playing = queue.now_playing.title
    # queue_str = f"Now Playing: **{now_playing}**\n"
    # count = 1

    # if len(songs) > 0:
    #     for song in songs:
    #         queue_str += f"{count}. **{song.title}**" + "\n"
        
    #     await interaction.response.send_message(f"🔥🎶 **Music Queue** 🎶🔥" + "\n" + "--------------------------------------------\n" + queue_str)
    # else: 
    #     await interaction.response.send_message(f"🔥🎶 The music queue is empty! Add songs with **/play!** 🎶🔥")
    embed = await CalciferMusicEmbed.queue_embed(queue)
    await interaction.response.send_message(embed=embed)

@calcifer.tree.command(name="stop", description="Stop the queue completely and disconnect!")
async def stop(interaction: discord.Interaction):
    try:
        music_session = await calcifer.get_music_session(interaction)
        queue: Queue = music_session.queue
        await queue.stop()
        calcifer.sessions.remove(music_session)
        await interaction.response.send_message("🔥 Stopped the queue and disconnected! 🔥")
    except QueueError:
        await interaction.response.send_message("🔥 Something went wrong! Could not stop queue, try disconnectiong manually! 🔥") 

@calcifer.tree.command(name="playlist", description="Play all songs from a youtube playlist!")
@app_commands.describe(url="url")
async def playlist(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    try:
        music_session = await calcifer.get_music_session(interaction)
        queue: Queue = music_session.queue
        playlist = await queue.playlist(interaction, url)
        resend = await music_session.embed.send_embed(interaction.channel)
        await interaction.followup.send(f'🔥 **"{playlist.title}"** playlist added **[{playlist.count}]** songs! 🔥')
    except PlaylistError as e:
        await interaction.followup.send(f"🔥 Something went wrong! Could not add songs from playlist provided! 🔥")

calcifer.run(token)