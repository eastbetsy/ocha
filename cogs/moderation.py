# cogs/moderation.py
import os
import discord
import psycopg2
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()

class ModerationCog(commands.Cog):
    """A cog for all moderation-related commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ----------------- WARN -----------------
    @app_commands.command(name="warn", description="Warn a member with a reason.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        cursor.execute(
            "INSERT INTO moderation_logs (guild_id, moderator_id, target_id, action_type, reason) VALUES (%s,%s,%s,%s,%s)",
            (interaction.guild.id, interaction.user.id, member.id, "warn", reason)
        )
        conn.commit()
        await interaction.response.send_message(f"⚠️ {member.mention} has been warned.\n**Reason:** {reason}", ephemeral=True)

    # ----------------- UNWARN -----------------
    @app_commands.command(name="unwarn", description="Remove a specific warning by ID")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def unwarn(self, interaction: discord.Interaction, warning_id: int):
        cursor.execute(
            "DELETE FROM moderation_logs WHERE id=%s AND action_type='warn' RETURNING id",
            (warning_id,)
        )
        deleted = cursor.fetchone()
        conn.commit()
        if deleted:
            await interaction.response.send_message(f"✅ Successfully removed warning ID `{warning_id}`.", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ Warning ID `{warning_id}` not found.", ephemeral=True)

    # ----------------- BAN -----------------
    @app_commands.command(name="ban", description="Permanently bans a member from the server.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        if member.top_role >= interaction.user.top_role and interaction.guild.owner != interaction.user:
            await interaction.response.send_message("You cannot ban a member with an equal or higher role than you.", ephemeral=True)
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I cannot ban this member because their role is higher than mine.", ephemeral=True)
            return
        try:
            await interaction.guild.ban(member, reason=reason)
            cursor.execute(
                "INSERT INTO moderation_logs (guild_id, moderator_id, target_id, action_type, reason) VALUES (%s,%s,%s,%s,%s)",
                (interaction.guild.id, interaction.user.id, member.id, "ban", reason)
            )
            conn.commit()
            await interaction.response.send_message(f"✅ {member.mention} has been banned. Reason: **{reason}**")
        except discord.Forbidden:
            await interaction.response.send_message("❌ I do not have permission to ban that member.", ephemeral=True)

    # ----------------- KICK -----------------
    @app_commands.command(name="kick", description="Kicks a member from the server.")
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
            cursor.execute(
                "INSERT INTO moderation_logs (guild_id, moderator_id, target_id, action_type, reason) VALUES (%s,%s,%s,%s,%s)",
                (interaction.guild.id, interaction.user.id, member.id, "kick", reason)
            )
            conn.commit()
            await interaction.response.send_message(f"✅ {member.mention} has been kicked. Reason: **{reason}**")
        except discord.Forbidden:
            await interaction.response.send_message("❌ I do not have permission to kick that member.", ephemeral=True)

    # ----------------- UNBAN -----------------
    @app_commands.command(name="unban", description="Unbans a member.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        try:
            await interaction.guild.unban(member, reason=reason)
            cursor.execute(
                "INSERT INTO moderation_logs (guild_id, moderator_id, target_id, action_type, reason) VALUES (%s,%s,%s,%s,%s)",
                (interaction.guild.id, interaction.user.id, member.id, "unban", reason)
            )
            conn.commit()
            await interaction.response.send_message(f"✅ {member.mention} has been unbanned. Reason: **{reason}**")
        except discord.Forbidden:
            await interaction.response.send_message("❌ I do not have permission to unban that member.", ephemeral=True)

    # ----------------- WARNS QUERY -----------------
    @app_commands.command(name="warns", description="See a user's warning history.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warns(self, interaction: discord.Interaction, member: discord.Member):
        cursor.execute(
            "SELECT id, reason, timestamp FROM moderation_logs WHERE target_id=%s AND action_type='warn' ORDER BY timestamp DESC",
            (member.id,)
        )
        results = cursor.fetchall()
        if not results:
            await interaction.response.send_message(f"✅ {member.mention} has no warnings.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Warnings for {member.display_name}",
            color=discord.Color.orange()
        )
        for warn_id, reason, timestamp in results:
            embed.add_field(name=f"ID #{warn_id} | {timestamp.strftime('%Y-%m-%d %H:%M:%S')}", value=reason, inline=False)
        embed.set_footer(text=f"Total warnings: {len(results)}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ----------------- LOGS QUERY -----------------
    @app_commands.command(name="logs", description="See a user's full moderation history.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def logs(self, interaction: discord.Interaction, member: discord.Member):
        cursor.execute(
            "SELECT id, action_type, reason, timestamp FROM moderation_logs WHERE target_id=%s ORDER BY timestamp DESC",
            (member.id,)
        )
        results = cursor.fetchall()
        if not results:
            await interaction.response.send_message(f"✅ {member.mention} has no moderation history.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Moderation history for {member.display_name}",
            color=discord.Color.red()
        )
        for log_id, action, reason, timestamp in results:
            embed.add_field(name=f"ID #{log_id} | {action} | {timestamp.strftime('%Y-%m-%d %H:%M:%S')}", value=reason, inline=False)
        embed.set_footer(text=f"Total actions: {len(results)}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
