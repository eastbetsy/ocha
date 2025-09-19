import discord
from discord import app_commands
from discord.ext import commands

class DatabaseCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.supabase = bot.supabase_client

    @app_commands.command(name="register", description="Register your profile with the bot.")
    @app_commands.describe(username="Your desired username.")
    async def register(self, interaction: discord.Interaction, username: str):
        try:
            self.supabase.table("users").insert({
                "discord_id": interaction.user.id, 
                "username": username
            }).execute()
            await interaction.response.send_message(f"User `{username}` registered successfully!")
        except Exception as e:
            await interaction.response.send_message(f"Error: Could not register user. They may already exist.", ephemeral=True)
            print(e)

    @app_commands.command(name="profile", description="View your registered profile.")
    async def profile(self, interaction: discord.Interaction):
        try:
            response = self.supabase.table("users").select("*").eq("discord_id", interaction.user.id).execute()
            if response.data:
                user_data = response.data[0]
                await interaction.response.send_message(f"**Your Profile**\n- Username: `{user_data['username']}`\n- Discord ID: `{user_data['discord_id']}`")
            else:
                await interaction.response.send_message("You aren't registered. Use `/register` to create a profile.")
        except Exception as e:
            await interaction.response.send_message(f"Error retrieving profile: {e}", ephemeral=True)
            print(e)

async def setup(bot: commands.Bot):
    await bot.add_cog(DatabaseCog(bot))