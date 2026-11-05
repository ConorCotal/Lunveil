import discord
import asyncio
from ..UI import EmbedType
from config.Manager import ConfigManager

config = ConfigManager()

class ManageHandler:
    def __init__(self, bot, handlers):
        self.bot = bot
        self.handlers = handlers

    async def claim_ticket(self, interaction: discord.Interaction):
        await interaction.response.defer()
        thread = interaction.channel if isinstance(interaction.channel, discord.Thread) else None
        if thread is None:
            return

        # Lock thread during edit
        await thread.edit(locked=True)

        ticket_role = interaction.guild.get_role(config.NewTickets.Ticket_Role_ID)
        if not ticket_role:
            await thread.edit(locked=False)
            return

        # Remove members with the Ticket role except the claimer
        for member in thread.members:
            if member.id != interaction.user.id:
                full_member = interaction.guild.get_member(member.id)
                if full_member and ticket_role in full_member.roles:
                    try:
                        await thread.remove_user(member)
                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"Cannot remove member {member}: {e}")

        # Disable claim button - create a fresh view so we don't mutate the shared one
        try:
            from ..UI.buttons import button
            from utils import ButtonCreator

            # Build a fresh view with claim disabled but close still active
            new_view = ButtonCreator(
                button("Zajmij", discord.ButtonStyle.green, emoji="🏷️", custom_id="claim_ticket", row=0, disabled=True),
                button("Zamknij", discord.ButtonStyle.red, emoji="✖️", custom_id="close_ticket", row=0),
                callback=self.handlers.buttons.callback,
                persistent=False,
                bot=self.bot
            )
            await interaction.message.edit(view=new_view)
        except Exception as e:
            print(f"Error editing message view: {e}")

        # Unlock thread and remove slowmode
        await thread.edit(slowmode_delay=0, locked=False)
        
        claimed_embed = self.handlers.embeds.get(EmbedType.CLAIM, user=interaction.user)
        if claimed_embed:
            await thread.send(embed=claimed_embed)
        else:
            await thread.send(embed=discord.Embed(
                title=config.NewTickets.Messages.claimed.format(user=interaction.user.display_name),
                color=discord.Color.green()
            ))

    async def close_ticket(self, interaction: discord.Interaction):
        # Open modal to ask for closing reason
        await interaction.response.send_modal(self.handlers.modals.close_ticket_modal())

    async def handle_ticket_close(self, interaction: discord.Interaction):
        await interaction.response.defer()
        thread = interaction.channel if isinstance(interaction.channel, discord.Thread) else None
        if thread is None:
            return

        modal_values = interaction.data.get("modal_values", {})
        reason = modal_values.get("close_reason", "Brak powodu")

        # Send close embed
        close_embed = self.handlers.embeds.get(
            EmbedType.CLOSE, 
            user=interaction.user, 
            inputs={"field_1": reason}
        )
        await thread.send(embed=close_embed)

        # Remove from database
        thread_id = str(thread.id)
        if thread_id in self.bot.tickets_db:
            del self.bot.tickets_db[thread_id]
            await self.bot.tickets_db.save()

        # Lock and archive thread
        await thread.edit(archived=True, locked=True)
