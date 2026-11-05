import discord
from discord.ext import commands
from discord import app_commands

from utils import EmbedCreator, field, Colors

import random

class Roll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="roll",
        description="Rzuć kostką!"
    )
    async def roll(self, interaction: discord.Interaction):
        roll = random.randint(1, 20)

        embed = EmbedCreator(
            title="Rzut kostką!",
            description=f"Wyrzuciłeś: **{roll}**",
            color=Colors.PURPLE
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Roll(bot))