import discord
from music_queue import Queue

async def queue_embed(queue: Queue) -> discord.Embed:
    embed = discord.Embed(title="🔥🎶 Music Queue 🎶🔥")
    now_playing = await queue.get_now_playing()
    description = f"**Now Playing:** [ {now_playing.title} ]({now_playing.url}) - {now_playing.duration} \n"
    
    songs = queue.queue
    for x in range(len(songs)):
        description += f"**{x + 1}.** [{songs[x].title}]({songs[x].url}) - {songs[x].duration}\n"
    embed.description = description
    embed.colour = discord.Colour.dark_orange()
    embed.set_footer(text="Calcifer",icon_url=None)
    embed.set_thumbnail(url=queue.now_playing.thumbnail)
    embed.thumbnail.height = 500
    embed.thumbnail.width = 500
    return embed

