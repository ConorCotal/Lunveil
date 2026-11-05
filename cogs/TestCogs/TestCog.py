import discord
from discord.ext import commands
from discord import app_commands

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(
        name="test",
        description="Test command."
    )
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message("test")

async def setup(bot):
    await bot.add_cog(TestCog(bot))