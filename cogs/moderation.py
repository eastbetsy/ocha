import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone

class ModerationCog(commands.Cog):
    """A cog for all moderation-related commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.supabase = bot.supabase_client

    # --- BAN COMMAND ---
    @app_commands.command(name="ban", description="Permanently bans a member from the server.")
    @app_commands.describe(member="The member to ban.", reason="The reason for the ban.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        # Check if the user is trying to ban someone with an equal or higher role
        if member.top_role >= interaction.user.top_role and interaction.guild.owner != interaction.user:
             await interaction.response.send_message("You cannot ban a member with an equal or higher role than you.", ephemeral=True)
             return
        # Check if the bot can ban the user
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I cannot ban this member because their role is higher than mine.", ephemeral=True)
            return

        try:
            await interaction.guild.ban(member, reason=reason)
            
            log_data = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "guild_id": interaction.guild.id, "moderator_id": interaction.user.id,
                "target_id": member.id, "action_type": "ban", "reason": reason,
            }
            await self.bot.loop.run_in_executor(None, lambda: self.supabase.table("moderation_logs").insert(log_data).execute())
            
            await interaction.response.send_message(f'✅ {member.mention} has been permanently banned. Reason: **{reason}**')
        except discord.Forbidden:
            await interaction.response.send_message("❌ **I do not have permission to ban that member.**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An unexpected error occurred: {e}", ephemeral=True)

    @ban.error
    async def on_ban_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You don't have the `Ban Members` permission to use this.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An unknown error occurred: {error}", ephemeral=True)

    # --- KICK COMMAND ---
    @app_commands.command(name="kick", description="Kicks a member from the server.")
    @app_commands.describe(member="The member to kick.", reason="The reason for the kick.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        if member.top_role >= interaction.user.top_role and interaction.guild.owner != interaction.user:
             await interaction.response.send_message("You cannot kick a member with an equal or higher role than you.", ephemeral=True)
             return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I cannot kick this member because their role is higher than mine.", ephemeral=True)
            return

        try:
            await member.kick(reason=reason)
            
            log_data = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "guild_id": interaction.guild.id, "moderator_id": interaction.user.id,
                "target_id": member.id, "action_type": "kick", "reason": reason,
            }
            await self.bot.loop.run_in_executor(None, lambda: self.supabase.table("moderation_logs").insert(log_data).execute())
            
            await interaction.response.send_message(f'✅ {member.mention} has been kicked. Reason: **{reason}**')
        except discord.Forbidden:
            await interaction.response.send_message("❌ **I do not have permission to kick that member.**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An unexpected error occurred: {e}", ephemeral=True)

    @kick.error
    async def on_kick_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You don't have the `Kick Members` permission for this.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An unknown error occurred: {error}", ephemeral=True)

    # --- WARN COMMAND ---
    @app_commands.command(name="warn", description="Warns a member and logs it.")
    @app_commands.describe(member="The member to warn.", reason="The reason for the warning.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        if member.bot:
            await interaction.response.send_message("You cannot warn a bot.", ephemeral=True)
            return

        embed = discord.Embed(
            title="⚠️ You have been warned!",
            description=f"**Server:** {interaction.guild.name}\n**Reason:** {reason}",
            color=discord.Color.orange()
        )
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message(f"Could not DM {member.mention}, but the warning will still be logged.")
        
        try:
            log_data = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "guild_id": interaction.guild.id, "moderator_id": interaction.user.id,
                "target_id": member.id, "action_type": "warn", "reason": reason,
            }
            await self.bot.loop.run_in_executor(None, lambda: self.supabase.table("moderation_logs").insert(log_data).execute())

            await interaction.response.send_message(f'{member.mention} has been warned for: **{reason}**')
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while logging the warn: {e}", ephemeral=True)
    
    @warn.error
    async def on_warn_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You don't have the `Kick Members` permission to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An unknown error occurred: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))