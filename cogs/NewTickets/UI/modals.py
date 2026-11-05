import discord
from datetime import datetime, timezone, timedelta
from utils import ModalCreator, ModalInput, ModalInputType
from config.Manager import ConfigManager

config = ConfigManager()

class Modals:
    def __init__(self, bot, handlers):
        self.bot = bot
        self.handlers = handlers
        self.debug = False  # Set to False in production
        
        self.handler_map = {
            "close_ticket_modal": self.handlers.handle_ticket_close,
            "event_ticket_modal": self.handlers.handle_event_ticket,
            "help_ticket_modal": self.handlers.handle_help_ticket,
            "ck_ticket_modal": self.handlers.handle_ck_ticket,
            "report_player_ticket_modal": self.handlers.handle_report_player_ticket,
            "report_error_ticket_modal": self.handlers.handle_report_error_ticket,
            "contact_ticket_modal": self.handlers.handle_contact_ticket
        }

    def close_ticket_modal(self):
        return ModalCreator(
            title="Ticket > Zamknięcie ❌",
            action_id="close_ticket_modal",
            inputs=[
                ModalInput(
                    type=ModalInputType.TEXT,
                    label="Powód Zamknięcia",
                    custom_id="close_reason",
                    placeholder="Tu wpisz powód zamknięcia..",
                    required=True,
                    default="[DEBUG] Powód zamknięcia..." if self.debug else None
                )
            ],
            callback=self.callback
        )

    def event_ticket_modal(self):
        return ModalCreator(
            title="Ticket > Podanie o Event 🎉",
            action_id="event_ticket_modal",
            inputs=[
                ModalInput(
                    type=ModalInputType.TEXT,
                    label="Nickname Minecraft",
                    custom_id="field_1",
                    placeholder="Tu wpisz swój nickname Minecraft..",
                    max_length=16,
                    min_length=2,
                    required=True,
                    default="RinPlay" if self.debug else None
                ),
                ModalInput(
                    type=ModalInputType.TEXT,
                    label="Data",
                    custom_id="field_2",
                    placeholder="Tu wpisz datę eventu..",
                    max_length=21,
                    min_length=10,
                    required=True,
                    default=datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=2))).strftime("%d-%m | %H:%M")
                ),
                ModalInput(
                    type=ModalInputType.SELECT,
                    label="Rodzaj Eventu",
                    custom_id="field_3",
                    required=True,
                    options=[
                        discord.SelectOption(label="Lokalny", value="Lokalny"),
                        discord.SelectOption(label="Globalny", value="Globalny")
                    ]
                ),
                ModalInput(
                    type=ModalInputType.CHECKBOX,
                    label="Potrzebny GM",
                    custom_id="field_4"
                ),
                ModalInput(
                    type=ModalInputType.TEXT,
                    label="Pomysł na Event",
                    custom_id="field_5",
                    placeholder="Tu wpisz treść..",
                    min_length=14,
                    required=True,
                    default="[DEBUG] Opis eventu..." if self.debug else None,
                    style=discord.TextStyle.long
                )
            ],
            callback=self.callback
        )

    def help_ticket_modal(self):
        return ModalCreator(
            title="Ticket > Potrzebuję Pomocy 🙏",
            action_id="help_ticket_modal",
            inputs=[
                ModalInput(
                    type=ModalInputType.TEXT,
                    label="Nickname Minecraft",
                    custom_id="field_1",
                    placeholder="Tu wpisz swój nickname Minecraft..",
                    max_length=16,
                    min_length=2,
                    required=True,
                    default="RinPlay" if self.debug else None
                ),
                ModalInput(
                    type=ModalInputType.TEXT,
                    label="Szczegóły Zgłoszenia",
                    custom_id="field_2",
                    placeholder="Tu wpisz treść..",
                    min_length=14,
                    required=True,
                    default="[DEBUG] Szczegóły zgłoszenia..." if self.debug else None,
                    style=discord.TextStyle.long
                ),
                ModalInput(
                    type=ModalInputType.TEXT,
                    label="Próby Rozwiązania",
                    custom_id="field_3",
                    placeholder="Tu wpisz treść..",
                    min_length=14,
                    required=True,
                    default="[DEBUG] Próby rozwiązania..." if self.debug else None,
                    style=discord.TextStyle.long
                )
            ],
            callback=self.callback
        )

    def ck_ticket_modal(self):
        return ModalCreator(
            title="Ticket > Character Kill 💀",
            action_id="ck_ticket_modal",
            inputs=[
                ModalInput(
                    type=ModalInputType.TEXT,
                    label="Nickname Minecraft",
                    custom_id="field_1",
                    placeholder="Tu wpisz swój nickname Minecraft..",
                    max_length=16,
                    min_length=2,
                    required=True,
                    default="RinPlay" if self.debug else None
                ),
                ModalInput(
                    type=ModalInputType.USER,
                    label="Oponent (Discord)",
                    custom_id="field_2",
                    placeholder="Wybierz oponenta...",
                    required=False
                ),
                ModalInput(
                    type=ModalInputType.CHECKBOX,
                    label="Potrzebny GM",
                    custom_id="field_3"
                ),
                ModalInput(
                    type=ModalInputType.TEXT,
                    label="Jak postać ma umrzeć?",
                    custom_id="field_4",
                    placeholder="Tu wpisz treść..",
                    min_length=14,
                    required=True,
                    default="[DEBUG] Opis śmierci..." if self.debug else None,
                    style=discord.TextStyle.long
                )
            ],
            callback=self.callback
        )

    def report_player_ticket_modal(self):
        return ModalCreator(
            title="Ticket > Zgłoszenie Gracza 👤",
            action_id="report_player_ticket_modal",
            inputs=[
                ModalInput(
                    type=ModalInputType.USER,
                    label="Zgłaszany Gracz (Discord)",
                    custom_id="field_1",
                    placeholder="Wybierz gracza...",
                    required=True
                ),
                ModalInput(
                    type=ModalInputType.TEXT,
                    label="Szczegóły Zgłoszenia",
                    custom_id="field_2",
                    placeholder="Tu wpisz treść..",
                    min_length=14,
                    required=True,
                    default="[DEBUG] Szczegóły zgłoszenia..." if self.debug else None,
                    style=discord.TextStyle.long
                )
            ],
            callback=self.callback
        )

    def report_error_ticket_modal(self):
        return ModalCreator(
            title="Ticket > Zgłoszenie Błędu 👾",
            action_id="report_error_ticket_modal",
            inputs=[
                ModalInput(
                    type=ModalInputType.TEXT,
                    label="Szczegóły Zgłoszenia",
                    custom_id="field_1",
                    placeholder="Tu wpisz treść..",
                    min_length=14,
                    required=True,
                    default="[DEBUG] Szczegóły zgłoszenia..." if self.debug else None,
                    style=discord.TextStyle.long
                )
            ],
            callback=self.callback
        )

    def contact_ticket_modal(self):
        return ModalCreator(
            title="Ticket > Kontakt ✉️",
            action_id="contact_ticket_modal",
            inputs=[
                ModalInput(
                    type=ModalInputType.TEXT,
                    label="Temat",
                    custom_id="field_1",
                    placeholder="Tu wpisz temat wiadomości..",
                    max_length=50,
                    min_length=2,
                    required=True,
                    default="Kontakt w sprawie..." if self.debug else None
                ),
                ModalInput(
                    type=ModalInputType.TEXT,
                    label="Treść",
                    custom_id="field_2",
                    placeholder="Tu wpisz treść wiadomości..",
                    min_length=14,
                    required=True,
                    default="[DEBUG] Treść wiadomości..." if self.debug else None,
                    style=discord.TextStyle.long
                )
            ],
            callback=self.callback
        )

    async def callback(self, interaction: discord.Interaction, data):
        try:
            action_id = interaction.data.get("custom_id")
            handler = self.handler_map.get(action_id)

            if handler:
                interaction.data["modal_values"] = data
                result = handler(interaction)
                if hasattr(result, "__await__"):
                    await result
            else:
                await interaction.response.send_message(
                    config.NewTickets.Messages.system_error,
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error in universal modal callback for Tickets: {e}")
