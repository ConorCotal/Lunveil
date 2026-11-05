import discord
from utils import ButtonCreator, button, get_button_style
from config.Manager import ConfigManager

config = ConfigManager()

class Buttons:
    def __init__(self, bot, handlers):
        self.bot = bot
        self.handlers = handlers
        
        self.handler_map = {
            "event_ticket": self.handlers.show_event_modal,
            "help_ticket": self.handlers.show_help_modal,
            "ck_ticket": self.handlers.show_ck_modal,
            "report_player_ticket": self.handlers.show_report_player_modal,
            "report_error_ticket": self.handlers.show_report_error_modal,
            "contact_ticket": self.handlers.show_contact_modal,
            "claim_ticket": self.handlers.claim_ticket,
            "close_ticket": self.handlers.close_ticket
        }
        self.create()

    def create(self):
        self.service_view = ButtonCreator(
            button("Zajmij", discord.ButtonStyle.green, emoji="🏷️", custom_id="claim_ticket", row=0),
            button("Zamknij", discord.ButtonStyle.red, emoji="✖️", custom_id="close_ticket", row=0),
            callback=self.callback,
            persistent=True,
            bot=self.bot
        )

        self.mc_view = ButtonCreator(
            button("Podanie o Event", discord.ButtonStyle.green, emoji="🎉", custom_id="event_ticket", row=0),
            button("Potrzebuję Pomocy", discord.ButtonStyle.blurple, emoji="🙏", custom_id="help_ticket", row=0),
            callback=self.callback,
            persistent=True,
            bot=self.bot
        )

        self.other_view = ButtonCreator(
            button("Zgłoś Gracza", discord.ButtonStyle.red, emoji="👤", custom_id="report_player_ticket", row=0),
            button("Zgłoś Błąd", discord.ButtonStyle.red, emoji="👾", custom_id="report_error_ticket", row=0),
            button("Kontakt", discord.ButtonStyle.blurple, emoji="✉️", custom_id="contact_ticket", row=1),
            callback=self.callback,
            persistent=True,
            bot=self.bot
        )

    async def callback(self, interaction: discord.Interaction, btn: button):
        try:
            # Only users with the Ticket role can use service buttons inside ticket threads (Zajmij/Zamknij)
            if btn.custom_id in ("claim_ticket", "close_ticket"):
                ticket_role = interaction.guild.get_role(config.NewTickets.Ticket_Role_ID)
                if ticket_role and ticket_role not in interaction.user.roles:
                    await interaction.response.send_message(
                        "Nie masz uprawnień do korzystania z tego przycisku.",
                        ephemeral=True
                    )
                    return

            handler = self.handler_map.get(btn.custom_id)
            if handler:
                result = handler(interaction)
                if hasattr(result, "__await__"):
                    await result
            else:
                await interaction.response.send_message(
                    config.NewTickets.Messages.unknown_button,
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error in button callback for Tickets: {e}")
