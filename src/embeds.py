import discord
from music_queue import Queue

class CalciferMusicEmbed(discord.Embed):
    def __init__(self, client: discord.Client, resend_amount, queue: Queue):
        self.client = client
        self.message: discord.Message = None
        self.queue = queue
        self.resend_amount = resend_amount
        self.message_count = 0
        self.colour = discord.Colour.dark_orange()
        self.title = "🔥🎶 Now Playing 🎶🔥"
        self.type = "rich"
        self.url = None
        self.timestamp = None
    
    async def send_embed(self, text_channel: discord.TextChannel):
        now_playing = self.queue.now_playing
        description = f"### {now_playing.title} - ({now_playing.duration}) \n Added by {now_playing.member.display_name}"
        if self.message_count >= self.resend_amount or self.message == None:
            self.message_count = 0
            if self.message != None:
                try:
                    await self.message.delete()
                except Exception as e:
                    raise Exception(f"Could not delete embed message {e}")
            self.set_image(url=now_playing.thumbnail)
            self.description = description
            try:
                self.message = await text_channel.send(embed=self)
            except Exception as e:
                raise Exception(f"Could not send embed {e}")
            return True
        else:
            embed = self.message.embeds[0]
            embed.set_image(url=now_playing.thumbnail)
            embed.description = description
            await self.message.edit(embed=embed)
        return False
        
    @staticmethod
    async def queue_embed(queue) -> discord.Embed:
        embed = discord.Embed(title="🔥🎶 Music Queue 🎶🔥")
        now_playing = await queue.get_now_playing()
        description = f"**Now Playing:** [ {now_playing.title} ]({now_playing.url}) - {now_playing.duration} \n"
        
        songs = queue.songs
        for x in range(len(songs)):
            description += f"**{x + 1}.** [{songs[x].title}]({songs[x].url}) - {songs[x].duration}\n"
        embed.description = description
        embed.colour = discord.Colour.dark_orange()
        embed.set_footer(text="Calcifer",icon_url=None)
        embed.set_thumbnail(url=queue.now_playing.thumbnail)
        return embed

