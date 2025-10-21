import discord
from discord.ext import commands

class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Sets the bot's presence.
        print("Bot is ready, changing presence...")
        game = discord.Game("gentalks.vercel.app")
        await self.bot.change_presence(status=discord.Status.online, activity=game)
        print("Presence has been set.")

    @discord.app_commands.command(name="member_count", description="View number of total members in this server.")
    async def member_count(self, interaction: discord.Interaction):
        guild = interaction.guild
        await interaction.response.send_message(f"**{guild.name}** currently has **{guild.member_count}** members.")

async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
