import discord
from discord.ext import commands
import discord.ext.commands
import discord.ext
from music_queue.queue import Queue, QueueError, find_or_add_queue, queues


class Music(commands.Cog):
    
    def __init__(self, bot):
        self.bot: discord.Bot = bot
        

    @discord.slash_command()
    async def ping(self, ctx):
        await ctx.send_response("Pong!")

    @discord.slash_command()
    async def play(self, ctx, query: str):
        try:
            voice_channel = ctx.author.voice.channel
        except:
            await ctx.send_response("🔥 You need to connect to a voice channel first! 🔥")
            return
        
        queue: Queue = await find_or_add_queue(self.bot, ctx.author.guild.id)
        
        if queue.paused:
            #the pause function is also for resuming
            await queue.pause()
        else:

            try:
                song = await queue.add_to_queue(ctx, query)

                await ctx.send_response(f"🔥 **'{song.title}'** was added to the queue! 🔥")
            except QueueError:
                await ctx.send_response("🔥 Could not play the song, either because of incorrect format(playlist or livestream) or search yielded no results, try another keyword/url! 🔥")
    @discord.slash_command()
    async def pause(self, ctx):
        try:
            queue: Queue = await find_or_add_queue(self.bot, ctx.author.guild.id)
            await queue.pause()
            if queue.paused:
                await ctx.send_response(f"🔥 Paused the queue! 🔥")
            elif not queue.paused:
                await ctx.send_response(f"🔥 Resumed the queue! 🔥")
        except QueueError:
            await ctx.send_response(f"🔥 Something went wrong! Could not pause the queue! 🔥")


    @discord.slash_command()
    async def skip(self, ctx):
        try:
            queue: Queue = await find_or_add_queue(self.bot, ctx.author.guild.id)
            if len(queue.queue) > 0:
                await queue.skip()
                await ctx.send_response(f"🔥 Skipped to the next song in queue! 🔥")
            else:
                await queue.stop()
                await ctx.send_response(f"🔥 Queue was empty! Now disconnecting... 🔥")
        except QueueError:
            await ctx.send_response(f"🔥 Something went wrong! Could not skip to next song! 🔥")

    @discord.slash_command()
    async def queue(self, ctx):
        queue: Queue = await find_or_add_queue(self.bot, ctx.author.guild.id)
        songs = await queue.get_queue()
        queue_str = ""
        count = 1

        if len(songs) > 0:
            for song in songs:
                queue_str += f"{count}. **{song.title}**" + "\n"
            
            await ctx.send_response(f"🔥🎶 **Music Queue** 🔥🎶🎶🔥" + "\n" + "--------------------------------------------\n" + queue_str)
        else: 
            await ctx.send_response(f"🔥🎶 The music queue is empty! Add songs with **/play!** 🎶🔥")

    @discord.slash_command()
    async def stop(self, ctx):
        try:
            queue: Queue = await find_or_add_queue(self.bot, ctx.author.guild.id)
            await queue.stop()
            await ctx.send_response("🔥 Stopped the queue and disconnected! 🔥")
        except QueueError:
            await ctx.send_response("🔥 Something went wrong! Could not stop queue, try disconnectiong manually! 🔥")

    @discord.slash_command()
    async def queuez(self, ctx):
        for q in queues:
            print(q.guild_id)
        await ctx.send_response("Testing...")
def setup(bot):
    bot.add_cog(Music(bot))

        


    

            
