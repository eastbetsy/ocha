import discord
import logging
import os
from dotenv import load_dotenv
from discord.ext import commands


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# declare intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

#setup logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# create client
bot = commands.Bot(command_prefix='o!', intents=intents)
# define welcome channel
welcome_channel_id = 1417664212645314655
# create events

# login to client
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'We have logged in as {bot.user}')
    print('Slash commands have been synced!')

# auto send message to specific channel when user joins server
@bot.event
async def on_member_join(member):
    print("A new member joined the server.")
    channel = bot.get_channel(welcome_channel_id)
    if channel:
        await channel.send(f"Welcome {member.mention} to **{member.guild.name}**! 👋")
    else:
       print('Specified channel does not exist.')

# commands
@bot.tree.command(name="welcome", description="Sends a welcome message.")
async def welcome_message(interaction: discord.Interaction):
    await interaction.response.send_message("Welcome to GenTalks! Please read the rules thoroughly and have a fun time~ <#1361929072158179479>")
    
@bot.tree.command(name="member_count", description="View number of total members in this server.")
async def member_count(interaction: discord.Interaction):
    # total server member count
    guild = interaction.guild
    member_count = guild.member_count
    await interaction.response.send_message(f"**{guild.name}** currently has **{member_count}** members.")



discord.utils.setup_logging(level=logging.INFO, root=False)
bot.run(TOKEN)