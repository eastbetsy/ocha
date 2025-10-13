import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import time
import os

class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldowns = {}
        
        if not os.path.exists('database'):
            os.makedirs('database')
            
        self.db = sqlite3.connect('database/levels.db')
        self.cursor = self.db.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                guild_id INTEGER,
                user_id INTEGER,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        self.db.commit()

    def cog_unload(self):
        self.db.close()

    def calculate_xp_for_next_level(self, level: int):
        return 5 * (level ** 2) + 50 * level + 100

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        guild_id = message.guild.id
        current_time = time.time()
        
        if user_id in self.cooldowns:
            if current_time - self.cooldowns[user_id] < 60:
                return
        
        self.cooldowns[user_id] = current_time

        xp_to_add = random.randint(15, 25)
        self.cursor.execute("SELECT * FROM users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        user_data = self.cursor.fetchone()

        if user_data is None:
            self.cursor.execute("INSERT INTO users (guild_id, user_id, xp, level) VALUES (?, ?, ?, ?)",
                                (guild_id, user_id, xp_to_add, 1))
            current_xp = xp_to_add
            current_level = 1
        else:
            current_xp = user_data[2] + xp_to_add
            current_level = user_data[3]
            self.cursor.execute("UPDATE users SET xp = ? WHERE guild_id = ? AND user_id = ?",
                                (current_xp, guild_id, user_id))
        
        self.db.commit()

        xp_needed = self.calculate_xp_for_next_level(current_level)
        if current_xp >= xp_needed:
            new_level = current_level + 1
            self.cursor.execute("UPDATE users SET level = ? WHERE guild_id = ? AND user_id = ?",
                                (new_level, guild_id, user_id))
            self.db.commit()
            try:
                await message.channel.send(f"🎉 Congrats {message.author.mention}, you've reached **Level {new_level}**!")
            except discord.Forbidden:
                pass

    @app_commands.command(name="rank", description="Check your or another member's rank and level.")
    @app_commands.describe(member="The member you want to check the rank of.")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        target_user = member or interaction.user
        guild_id = interaction.guild.id
        user_id = target_user.id

        self.cursor.execute("SELECT xp, level FROM users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        user_data = self.cursor.fetchone()

        if user_data is None:
            await interaction.response.send_message(f"{target_user.display_name} hasn't earned any XP yet.", ephemeral=True)
            return
            
        xp, level = user_data
        xp_needed_for_next = self.calculate_xp_for_next_level(level)
        
        embed = discord.Embed(title=f"🏆 Rank for {target_user.display_name}", color=target_user.color)
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="XP", value=f"**{xp} / {xp_needed_for_next}**", inline=True)
        
        bar_length = 15
        progress = int((xp / xp_needed_for_next) * bar_length)
        bar = "🟩" * progress + "─" * (bar_length - progress)
        embed.add_field(name="Progress to Next Level", value=f"`{bar}`", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Shows the server's XP leaderboard.")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        
        self.cursor.execute("SELECT user_id, level, xp FROM users WHERE guild_id = ? ORDER BY xp DESC LIMIT 10", (guild_id,))
        top_users = self.cursor.fetchall()

        if not top_users:
            await interaction.response.send_message("There's no one on the leaderboard yet!", ephemeral=True)
            return

        embed = discord.Embed(title=f"🏆 Leaderboard for {interaction.guild.name}", color=discord.Color.gold())
        
        description = ""
        for rank, (user_id, level, xp) in enumerate(top_users, start=1):
            user = interaction.guild.get_member(user_id)
            user_display = user.mention if user else f"_(Unknown User ID: {user_id})_"
            
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**{rank}.**"
            description += f"{emoji} {user_display} - **Level {level}** ({xp} XP)\n"
            
        embed.description = description
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
