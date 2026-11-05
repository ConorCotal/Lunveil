import discord
from discord.ext import commands
from discord import app_commands

from utils.JSONDataManager import JSONDataManager
from config.Manager import ConfigManager
from .handlers import Handlers

config = ConfigManager()

class NewTicketsModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.handlers = Handlers(bot)

        self.bot.tickets_db = JSONDataManager("cogs/NewTickets/database.json")

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(
        name="ticket-panel",
        description="Wysyła panel tworzenia ticketów."
    )
    async def ticket_panel(self, interaction: discord.Interaction):
        await self.handlers.send_ticket_panel(interaction)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread):
        if str(thread.id) in self.bot.tickets_db:
            del self.bot.tickets_db[str(thread.id)]
            await self.bot.tickets_db.save()

async def setup(bot):
    await bot.add_cog(NewTicketsModule(bot))
