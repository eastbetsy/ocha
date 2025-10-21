import os
import discord
from discord import app_commands
from discord.ext import commands
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone

class ModerationCog(commands.Cog):
    """A cog for all moderation-related commands using AWS RDS."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Connect to PostgreSQL
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", 5432),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

        # Create table if not exists
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS moderation_logs (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP,
            guild_id BIGINT,
            moderator_id BIGINT,
            target_id BIGINT,
            action_type TEXT,
            reason TEXT
        )
        """)
        self.conn.commit()

    # --- HELPER: log action ---
    async def log_action(self, guild_id, moderator_id, target_id, action_type, reason):
        now = datetime.now(timezone.utc)
        def db_op():
            self.cursor.execute(
                "INSERT INTO moderation_logs (created_at, guild_id, moderator_id, target_id, action_type, reason) VALUES (%s,%s,%s,%s,%s,%s)",
                (now, guild_id, moderator_id, target_id, action_type, reason)
            )
            self.conn.commit()
        await self.bot.loop.run_in_executor(None, db_op)

    # --- WARN COMMAND ---
    @app_commands.command(name="warn", description="Warn a member.")
    @app_commands.describe(member="The member to warn.", reason="The reason for the warning.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        await self.log_action(interaction.guild.id, interaction.user.id, member.id, "warn", reason)
        await interaction.response.send_message(f"⚠️ {member.mention} has been warned. Reason: **{reason}**")

    # --- UNWARN COMMAND ---
    @app_commands.command(name="unwarn", description="Remove a specific warning by ID.")
    @app_commands.describe(warning_id="The ID of the warning to remove.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def unwarn(self, interaction: discord.Interaction, warning_id: int):
        def db_op():
            self.cursor.execute("DELETE FROM moderation_logs WHERE id = %s AND action_type='warn' RETURNING *", (warning_id,))
            self.conn.commit()
            return self.cursor.fetchone()
        deleted = await self.bot.loop.run_in_executor(None, db_op)
        if deleted:
            await interaction.response.send_message(f"✅ Warning {warning_id} removed successfully.")
        else:
            await interaction.response.send_message(f"⚠️ Warning {warning_id} not found.")

    # --- BAN COMMAND ---
    @app_commands.command(name="ban", description="Permanently bans a member.")
    @app_commands.describe(member="The member to ban.", reason="The reason for the ban.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        try:
            await interaction.guild.ban(member, reason=reason)
            await self.log_action(interaction.guild.id, interaction.user.id, member.id, "ban", reason)
            await interaction.response.send_message(f"✅ {member.mention} has been banned. Reason: **{reason}**")
        except discord.Forbidden:
            await interaction.response.send_message("❌ I cannot ban that member.", ephemeral=True)

    # --- KICK COMMAND ---
    @app_commands.command(name="kick", description="Kicks a member.")
    @app_commands.describe(member="The member to kick.", reason="The reason for the kick.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        try:
            await member.kick(reason=reason)
            await self.log_action(interaction.guild.id, interaction.user.id, member.id, "kick", reason)
            await interaction.response.send_message(f"✅ {member.mention} has been kicked. Reason: **{reason}**")
        except discord.Forbidden:
            await interaction.response.send_message("❌ I cannot kick that member.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
