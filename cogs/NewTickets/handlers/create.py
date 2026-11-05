import discord
import asyncio
from ..UI import EmbedType
from config.Manager import ConfigManager

config = ConfigManager()

class CreateHandler:
    def __init__(self, bot, handlers):
        self.bot = bot
        self.handlers = handlers

    async def send_ticket_panel(self, interaction: discord.Interaction):
        await interaction.response.send_message(config.NewTickets.Messages.sending_panel, ephemeral=True)
        
        mc_picture = discord.File("images/MC_icon.png", filename="MC_icon.png")
        sep_line = discord.File("images/sep_line.png", filename="sep_line.png")
        other_picture = discord.File("images/DC_icon.png", filename="DC_icon.png")
        
        mc_ticket = self.handlers.embeds.get(EmbedType.MC_TICKET, thumbnail="attachment://MC_icon.png")
        other_ticket = self.handlers.embeds.get(EmbedType.OTHER_TICKET, thumbnail="attachment://DC_icon.png")
        
        await interaction.channel.send(embed=mc_ticket, file=mc_picture, view=self.handlers.buttons.mc_view)
        await interaction.channel.send(file=sep_line)
        await interaction.channel.send(embed=other_ticket, file=other_picture, view=self.handlers.buttons.other_view)

    async def show_event_modal(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.handlers.modals.event_ticket_modal())

    async def show_help_modal(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.handlers.modals.help_ticket_modal())

    async def show_ck_modal(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.handlers.modals.ck_ticket_modal())

    async def show_report_player_modal(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.handlers.modals.report_player_ticket_modal())

    async def show_report_error_modal(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.handlers.modals.report_error_ticket_modal())

    async def show_contact_modal(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.handlers.modals.contact_ticket_modal())

    # Submissions
    async def handle_event_ticket(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        modal_values = interaction.data.get("modal_values", {})
        await self.create_ticket_thread(interaction, "🎉", EmbedType.EVENT, modal_values)

    async def handle_help_ticket(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        modal_values = interaction.data.get("modal_values", {})
        await self.create_ticket_thread(interaction, "🙏", EmbedType.HELP, modal_values)

    async def handle_ck_ticket(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        modal_values = interaction.data.get("modal_values", {})
        await self.create_ticket_thread(interaction, "💀", EmbedType.CK, modal_values)

    async def handle_report_player_ticket(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        modal_values = interaction.data.get("modal_values", {})
        await self.create_ticket_thread(interaction, "👤", EmbedType.REPORT_PLAYER, modal_values)

    async def handle_report_error_ticket(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        modal_values = interaction.data.get("modal_values", {})
        await self.create_ticket_thread(interaction, "👾", EmbedType.REPORT_ERROR, modal_values)

    async def handle_contact_ticket(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        modal_values = interaction.data.get("modal_values", {})
        await self.create_ticket_thread(interaction, "✉️", EmbedType.CONTACT, modal_values)

    async def create_ticket_thread(self, interaction: discord.Interaction, ticket_type: str, embed_type: EmbedType, inputs: dict):
        ticket_role = interaction.guild.get_role(config.NewTickets.Ticket_Role_ID)
        debug_mode = getattr(self.handlers.modals, "debug", False)
        
        prefix = "[DEBUG] " if debug_mode else ""
        ticket_name = f"{prefix}{ticket_type} | {interaction.user.global_name}"

        try:
            if not isinstance(interaction.channel, discord.TextChannel):
                await interaction.followup.send(config.NewTickets.Messages.error_thread, ephemeral=True)
                return

            thread = await interaction.channel.create_thread(
                name=ticket_name,
                type=discord.ChannelType.private_thread,
                auto_archive_duration=10080,
                slowmode_delay=120,
                invitable=False
            )

            # Store mapping
            self.bot.tickets_db[thread.id] = interaction.user.id
            await self.bot.tickets_db.save()

            # Mention user and role then delete
            mention_message = await thread.send(f"{interaction.user.mention} {ticket_role.mention if ticket_role else ''}")
            await mention_message.delete()

            # Send embeds
            await thread.send(embed=self.handlers.embeds.get(EmbedType.INFO, user=interaction.user, inputs=inputs))
            await thread.send(embed=self.handlers.embeds.get(embed_type, user=interaction.user, inputs=inputs))
            await thread.send(embed=self.handlers.embeds.get(EmbedType.MESSAGE, user=interaction.user, inputs=inputs))
            await thread.send(embed=self.handlers.embeds.get(EmbedType.SERVICE, user=interaction.user, inputs=inputs), view=self.handlers.buttons.service_view)

            await interaction.followup.send(
                f"# Ticket został utworzony\n\n> {thread.mention} ◀ `[Kliknij Tutaj Aby Wejść]`",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error creating ticket: {e}")
            await interaction.followup.send(
                config.NewTickets.Messages.creator_error.format(error=e),
                ephemeral=True
            )
