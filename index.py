import nest_asyncio
nest_asyncio.apply()
import os
import discord
import logging
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(level=logging.INFO, root=False)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

bot = MyBot(command_prefix='o!', intents=intents)
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())