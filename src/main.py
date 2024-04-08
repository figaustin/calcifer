import os
import discord
from dotenv import load_dotenv
from music_queue.queue import Queue
load_dotenv()
token = str(os.getenv("TOKEN"))
bot = discord.Bot(intents=discord.Intents.all())

queues: list[Queue] = []

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

bot.load_extension('cogs.music_cog')
bot.run(token)