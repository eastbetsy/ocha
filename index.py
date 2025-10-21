import nest_asyncio
nest_asyncio.apply()

import os
import discord
import logging
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Logging setup
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(level=logging.INFO, root=False)

# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Bot definition
class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No Supabase; database connections handled in individual cogs via bot_db.py

bot = MyBot(command_prefix='o!', intents=intents)

# Load all cogs from ./cogs folder
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load cog {filename}: {e}")

# on_ready event
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Synced {len(bot.tree.walk_commands())} slash command(s).")
    print("------")

# Main entry
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

# Run the bot
if __name__ == "__main__":
    asyncio.run(main())
