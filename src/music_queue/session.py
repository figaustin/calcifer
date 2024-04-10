import discord
from music_queue.queue import Queue
from embeds import CalciferMusicEmbed

class MusicSession():
    def __init__(self, client, guild_id, interaction: discord.Interaction):
        self.client = client
        self.guild_id = guild_id
        self.queue: Queue = Queue(client, guild_id)
        self.interaction = interaction
        self.embed = CalciferMusicEmbed(client, 4, self.queue)



        


