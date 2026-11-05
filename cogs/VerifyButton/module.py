import discord
from discord.ext import commands
from discord import app_commands

from utils import ButtonCreator, button, get_button_style
from config.Manager import ConfigManager

config = ConfigManager()

class VerifyButton(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.button = ButtonCreator(
            button(label="Zweryfikuj się",
                   style=get_button_style("SUCCESS"),
                   custom_id="verify_button"),
            callback=self.callback,
            persistent=True,
            bot=self.bot
        )

    async def callback(self, interaction: discord.Interaction, btn: button):
        await interaction.user.add_roles(discord.Object(id=config.Verified_Role_ID))
        await interaction.response.send_message("Zostałeś zweryfikowany!", ephemeral=True)

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(
        name="verify-button",
        description="Verify a user."
    )
    async def verify_button(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.send(" ", view=self.button)

async def setup(bot):
    await bot.add_cog(VerifyButton(bot))