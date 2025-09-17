import discord
import logging
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# declare intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

#setup logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# create client
client = discord.Client(intents=intents)
# define welcome channel
welcome_channel_id = 1417664212645314655
# create events

# login to client
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

# auto send message to specific channel when user joins server
@client.event
async def on_member_join(member):
    print("A new member joined the server.")
    channel = client.get_channel(welcome_channel_id)
    if channel:
        await channel.send(f"Welcome {member.mention} to **{member.guild.name}**! 👋")
    else:
       print('Specified channel does not exist.')

# commands
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('o!greet'):
        await message.channel.send("Welcome to GenTalks! Please read the rules thoroughly and have a fun time~ <#1361929072158179479>")

    # total server member count
    if message.content.startswith('o!membercount'):
        guild = message.guild
        member_count = guild.member_count
        await message.channel.send(f"The server currently has **{member_count}** members.")
 
        



discord.utils.setup_logging(level=logging.INFO, root=False)
client.run(TOKEN)