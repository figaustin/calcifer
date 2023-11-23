import discord
import dotenv
import os
import asyncio

from discord.ext import commands
from cogs.music import MusicCog

dotenv.load_dotenv()

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='/', intents=intents)

async def main():
    async with bot:
        await bot.add_cog(MusicCog(bot))
        await bot.start(os.getenv('TOKEN'))

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced commands!")
    except Exception as e:
        print(f"Error syncing commands! {e}")

asyncio.run(main())