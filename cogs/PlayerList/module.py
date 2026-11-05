import discord
from discord.ext import commands
from discord import app_commands
from pathlib import Path

class PlayerList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(
        name="playerlist",
        description="Display the list of players."
    )
    async def playerlist(self, interaction: discord.Interaction):
        player_list = []
        for member in interaction.guild.members:
            if not member.bot:
                player_list.append(member.name)

        file_path = Path(__file__).resolve().parent / "player_list.txt"
        file_path.write_text("\n".join(player_list), encoding="utf-8")

        await interaction.response.send_message(
            f"Zapisano listę graczy do pliku `{file_path.name}`."
        )

# async def setup(bot):
#     await bot.add_cog(PlayerList(bot))