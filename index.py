import os
import discord
import logging
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from supabase import create_client, Client

async def main():
    load_dotenv()
    
    # Environment Variables
    TOKEN = os.getenv("DISCORD_TOKEN")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # Logging
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    discord.utils.setup_logging(level=logging.INFO, root=False)

    # Intents
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    # Bot and Supabase Initialization
    bot = commands.Bot(command_prefix='o!', intents=intents)
    bot.supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Load Cogs
    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user}')
        print('Syncing slash commands...')
        await bot.tree.sync()
        print('Commands synced!')

    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"Loaded cog: {filename}")

    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())