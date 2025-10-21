import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, time, timezone
import zoneinfo

# Constants
TARGET_TZ = zoneinfo.ZoneInfo("America/New_York")
ANNOUNCEMENT_TIME_UTC = time(12, 0)  # 12:00 PM EST

class ScheduledCheckinCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Guild/Channel/Role configuration
        self.guild_id = int(os.getenv("ANNOUNCE_GUILD_ID")) if os.getenv("ANNOUNCE_GUILD_ID") else None
        self.staff_channel_id = int(os.getenv("STAFF_CHANNEL_ID")) if os.getenv("STAFF_CHANNEL_ID") else None
        self.staff_role_id = int(os.getenv("STAFF_ROLE_ID")) if os.getenv("STAFF_ROLE_ID") else None

        self.scheduled_announcement.start()

    # --- HELPER FUNCTION ---
    async def _send_announcement_message(self):
        """Fetches channel/role, creates the embed, and sends the message."""
        if not self.staff_channel_id or not self.staff_role_id:
            print("Error: STAFF_CHANNEL_ID or STAFF_ROLE_ID not set in .env")
            return False

        channel = self.bot.get_channel(self.staff_channel_id)
        if not channel:
            print(f"Error: Could not find channel with ID {self.staff_channel_id}")
            return False

        if self.guild_id and channel.guild.id != self.guild_id:
            print(f"Skipping announcement: Channel guild {channel.guild.id} != configured guild {self.guild_id}")
            return False

        guild = channel.guild
        role = discord.utils.get(guild.roles, id=self.staff_role_id)
        if not role:
            print(f"Error: Could not find role with ID {self.staff_role_id}")
            return False

        announce_embed = discord.Embed(
            title="📅 **STAFF CHECK-IN DAY**",
            description="Hey staff! It's check-in day. Let us know how your week went!",
            color=discord.Color.orange()
        )

        try:
            await channel.send(content=role.mention, embed=announce_embed)
            print(f"✅ Successfully sent check-in message to #{channel.name}.")
            return True
        except Exception as e:
            print(f"Error sending check-in message: {e}")
            return False

    # --- SCHEDULED TASK ---
    @tasks.loop(minutes=1)
    async def scheduled_announcement(self):
        now_utc = datetime.now(timezone.utc)
        is_correct_day = now_utc.weekday() in [4]  # Friday
        is_correct_time = now_utc.hour == ANNOUNCEMENT_TIME_UTC.hour and now_utc.minute == ANNOUNCEMENT_TIME_UTC.minute

        if is_correct_day and is_correct_time:
            print("Scheduled time reached. Triggering announcement...")
            await self._send_announcement_message()

    @scheduled_announcement.before_loop
    async def before_scheduled_announcement(self):
        await self.bot.wait_until_ready()

    # --- MANUAL TEST COMMAND ---
    @app_commands.command(name="test_checkin", description="Manually triggers the check-in announcement for testing.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def test_checkin(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        print(f"Test command triggered by {interaction.user}.")
        success = await self._send_announcement_message()

        if success:
            await interaction.followup.send("✅ Test announcement sent successfully!")
        else:
            await interaction.followup.send("❌ Failed to send test announcement. Check the console for errors.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ScheduledCheckinCog(bot))
