import discord
from discord import app_commands
from discord.ext import commands

class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.supabase = bot.supabase_client

    @app_commands.command(name="warn", description="Warn a member.")
    @app_commands.describe(member="The member to warn.", reason="The reason for the warning.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        if member == interaction.user:
            await interaction.response.send_message("You cannot warn yourself.", ephemeral=True)
            return
        if member.bot:
            await interaction.response.send_message("You cannot warn a bot.", ephemeral=True)
            return

        try:
            embed = discord.Embed(
                title="⚠️ You have been warned!",
                description=f"**Server:** {interaction.guild.name}\n**Reason:** {reason}",
                color=discord.Color.blue()
            )
            await member.send(embed=embed)
            
            # Prepare the data to be inserted into Supabase
            log_data = {
                "guild_id": interaction.guild.id,
                "moderator_id": interaction.user.id,
                "target_id": member.id,
                "action_type": "warn",
                "reason": reason,
            }
            # Insert the log data into the 'moderation_logs' table
            self.supabase.table("moderation_logs").insert(log_data).execute()

            await interaction.response.send_message(f'{member.mention} has been warned for: **{reason}**')

        except discord.Forbidden:
            await interaction.response.send_message(f"Could not DM {member.mention}, but they have been warned.")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            print(e)

    @warn.error
    async def on_warn_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message("Something went wrong.", ephemeral=True)
            print(error)

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))