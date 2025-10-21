import os
import discord
import psycopg2
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import random
import time

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# PostgreSQL connection
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()

class Leveling(commands.Cog):
    """Cog to handle XP, leveling, ranks, and leaderboard."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldowns = {}  # (guild_id, user_id) -> timestamp

        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                guild_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        conn.commit()

    def cog_unload(self):
        cursor.close()
        conn.close()

    def calculate_xp_for_next_level(self, level: int):
        return 5 * (level ** 2) + 50 * level + 100

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        user_id = message.author.id
        current_time = time.time()

        key = (guild_id, user_id)
        if key in self.cooldowns and current_time - self.cooldowns[key] < 60:
            return

        self.cooldowns[key] = current_time
        xp_to_add = random.randint(15, 25)

        # Get current XP and level
        cursor.execute(
            "SELECT xp, level FROM users WHERE guild_id=%s AND user_id=%s",
            (guild_id, user_id)
        )
        row = cursor.fetchone()

        if row is None:
            current_xp = xp_to_add
            current_level = 1
            cursor.execute(
                "INSERT INTO users (guild_id, user_id, xp, level) VALUES (%s,%s,%s,%s)",
                (guild_id, user_id, current_xp, current_level)
            )
        else:
            current_xp, current_level = row
            current_xp += xp_to_add
            cursor.execute(
                "UPDATE users SET xp=%s WHERE guild_id=%s AND user_id=%s",
                (current_xp, guild_id, user_id)
            )

        # Handle multi-level up
        leveled_up = False
        while current_xp >= self.calculate_xp_for_next_level(current_level):
            current_xp -= self.calculate_xp_for_next_level(current_level)
            current_level += 1
            leveled_up = True
            cursor.execute(
                "UPDATE users SET level=%s, xp=%s WHERE guild_id=%s AND user_id=%s",
                (current_level, current_xp, guild_id, user_id)
            )

        conn.commit()

        if leveled_up:
            try:
                await message.channel.send(
                    f"🎉 Congrats {message.author.mention}, you've reached **Level {current_level}**!"
                )
            except discord.Forbidden:
                pass

    # ---------------- SLASH COMMANDS ----------------

    @app_commands.command(name="rank", description="Check your or another member's rank and level.")
    @app_commands.describe(member="The member you want to check the rank of.")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        if not interaction.guild:
            await interaction.response.send_message("This command only works in a server.", ephemeral=True)
            return

        target = member or interaction.user
        guild_id = interaction.guild.id
        user_id = target.id

        cursor.execute(
            "SELECT xp, level FROM users WHERE guild_id=%s AND user_id=%s",
            (guild_id, user_id)
        )
        row = cursor.fetchone()

        if row is None:
            await interaction.response.send_message(f"{target.display_name} hasn't earned any XP yet.", ephemeral=True)
            return

        xp, level = row
        xp_needed = self.calculate_xp_for_next_level(level)

        embed = discord.Embed(title=f"🏆 Rank for {target.display_name}", color=target.color)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="XP", value=f"**{xp} / {xp_needed}**", inline=True)

        bar_length = 15
        progress = int((xp / xp_needed) * bar_length)
        bar = "🟩" * progress + "─" * (bar_length - progress)
        embed.add_field(name="Progress to Next Level", value=f"`{bar}`", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Shows the server's XP leaderboard.")
    async def leaderboard(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command only works in a server.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        cursor.execute(
            "SELECT user_id, level, xp FROM users WHERE guild_id=%s ORDER BY level DESC, xp DESC LIMIT 10",
            (guild_id,)
        )
        rows = cursor.fetchall()

        if not rows:
            await interaction.response.send_message("There's no one on the leaderboard yet!", ephemeral=True)
            return

        embed = discord.Embed(title=f"🏆 Leaderboard for {interaction.guild.name}", color=discord.Color.gold())
        description = ""
        for rank, (user_id, level, xp) in enumerate(rows, start=1):
            user = interaction.guild.get_member(user_id)
            user_display = user.mention if user else f"_(Unknown User ID: {user_id})_"
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**{rank}.**"
            description += f"{emoji} {user_display} - **Level {level}** ({xp} XP)\n"

        embed.description = description
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
