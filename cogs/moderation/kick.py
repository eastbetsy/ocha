import discord
from discord import app_commands
from discord.ext import commands

class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.supabase = bot.supabase_client

@app_commands.command(name="kick", description="Kick a member.")
@app_commands.commands.describe(member="The member to kick.", reason="The reason for the kick.")
@app_commands.checks.has_permissions(kick_members=True)
async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
    guild = interaction.guild
    if member == interaction.user:
        await interaction.response.send_message("You cannot kick yourself.", ephemeral=True)
        return
    try:
        await member.send(f"You have been kicked from ${guild.name}")
    except discord.Forbidden:
            await interaction.response.send_message(f"Could not DM {member.mention}, but they have been kicked.")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
        print(e)
# connect to supabase
    log_data = {
        "guild_id": interaction.guild.id,
        "moderator_id": member.id,
        "action_type": "kick",
        "reason": reason,
    }
    self.supabase.table("moderation_logs").insert(log_data).execute()
# error message
    @warn.error
    async def on_warn_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message("Something went wrong.", ephemeral=True)
            print(error)
async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))