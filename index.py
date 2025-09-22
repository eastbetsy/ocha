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

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash command(s).')
    except Exception as e:
        print(f'Failed to sync commands: {e}')
    print('------')

async def main():
    async with bot:
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Successfully loaded cog: {filename}')
                except Exception as e:
                    print(f'Failed to load cog {filename}: {e}')
        
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shutdown requested. Exiting.")