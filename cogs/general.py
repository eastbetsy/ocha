import os
import discord
from discord.ext import commands

class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.welcome_channel_id = int(os.getenv("WELCOME_CHANNEL_ID"))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.bot.get_channel(self.welcome_channel_id)
        if channel:
            await channel.send(f"Welcome {member.mention} to **{member.guild.name}**! 👋 Please introduce yourself here.")
        else:
            print(f'Welcome channel with ID {self.welcome_channel_id} not found.')

    @discord.app_commands.command(name="welcome", description="Sends a welcome message.")
    async def welcome_message(self, interaction: discord.Interaction):
        await interaction.response.send_message("Welcome to GenTalks! Please read the rules thoroughly and introduce yourself.")

    @discord.app_commands.command(name="member_count", description="View number of total members in this server.")
    async def member_count(self, interaction: discord.Interaction):
        guild = interaction.guild
        await interaction.response.send_message(f"**{guild.name}** currently has **{guild.member_count}** members.")

async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))