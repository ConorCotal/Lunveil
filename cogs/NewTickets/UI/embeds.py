import discord
from enum import Enum
from config.Manager import ConfigManager
from utils import EmbedCreator, field, Colors

config = ConfigManager()
EmbCFG = config.NewTickets.Embeds

class EmbedType(Enum):
    MC_TICKET = 1
    OTHER_TICKET = 2
    INFO = 3
    MESSAGE = 4
    SERVICE = 5
    CLAIM = 6
    CLOSE = 7
    EVENT = 8
    HELP = 9
    CK = 10
    REPORT_PLAYER = 11
    REPORT_ERROR = 12
    CONTACT = 13

class Embeds:
    def __init__(self, bot):
        self.bot = bot

        self.embeds = {
            EmbedType.MC_TICKET: lambda **kwargs: EmbedCreator(
                title=EmbCFG.MC_TICKET.title,
                description=EmbCFG.MC_TICKET.description,
                color=Colors.get(EmbCFG.MC_TICKET.color),
                thumbnail=kwargs.get("thumbnail")
            ),
            EmbedType.OTHER_TICKET: lambda **kwargs: EmbedCreator(
                title=EmbCFG.OTHER_TICKET.title,
                description=EmbCFG.OTHER_TICKET.description,
                color=Colors.get(EmbCFG.OTHER_TICKET.color),
                thumbnail=kwargs.get("thumbnail")
            ),
            EmbedType.INFO: lambda **kwargs: EmbedCreator(
                title=EmbCFG.INFO.title,
                description=EmbCFG.INFO.description,
                color=Colors.get(EmbCFG.INFO.color),
                fields=[
                    field(f"Nickname: `{kwargs.get('user').name}`", f">>> Użytkownik: {kwargs.get('user').mention}\nID: `{kwargs.get('user').id}`", False),
                    field(
                        f"Dołączono: `{kwargs.get('user').joined_at.strftime('%d-%m-%Y %H:%M') if getattr(kwargs.get('user'), 'joined_at', None) else 'Nieznany'}`",
                        f"> Utworzono: `{kwargs.get('user').created_at.strftime('%d-%m-%Y %H:%M') if getattr(kwargs.get('user'), 'created_at', None) else 'Nieznany'}`",
                        False
                    )
                ],
                footer=EmbCFG.INFO.footer
            ),
            EmbedType.MESSAGE: lambda **kwargs: EmbedCreator(
                title=EmbCFG.MESSAGE.title,
                description=EmbCFG.MESSAGE.description,
                color=Colors.get(EmbCFG.MESSAGE.color),
                footer=EmbCFG.MESSAGE.footer
            ),
            EmbedType.SERVICE: lambda **kwargs: EmbedCreator(
                title=EmbCFG.SERVICE.title,
                description=EmbCFG.SERVICE.description,
                color=Colors.get(EmbCFG.SERVICE.color),
                footer=EmbCFG.SERVICE.footer
            ),
            EmbedType.CLAIM: lambda **kwargs: EmbedCreator(
                title=f"✅ **{kwargs.get('user').display_name}** zajął ticket!",
                color=Colors.get("GREEN")
            ),
            EmbedType.CLOSE: lambda **kwargs: EmbedCreator(
                title=EmbCFG.CLOSE.title.format(user=kwargs.get('user').display_name),
                description=EmbCFG.CLOSE.description.format(user=kwargs.get('user').mention),
                color=Colors.get(EmbCFG.CLOSE.color),
                fields=[
                    field("Powód:", f"```\n{kwargs.get('inputs', {}).get('field_1', 'Brak powodu')}\n```", False)
                ],
                footer=EmbCFG.CLOSE.footer
            ),
            EmbedType.EVENT: lambda **kwargs: EmbedCreator(
                title=EmbCFG.EVENT.title,
                description=EmbCFG.EVENT.description,
                color=Colors.get(EmbCFG.EVENT.color),
                fields=[
                    field("Nickname Minecraft", f">>> `{kwargs.get('inputs', {}).get('field_1')}`", False),
                    field("Data", f">>> `{kwargs.get('inputs', {}).get('field_2')}`", False),
                    field("Rodzaj Eventu", f">>> `{kwargs.get('inputs', {}).get('field_3')}`", False),
                    field("Potrzebny GM", f">>> `{'Tak' if kwargs.get('inputs', {}).get('field_4') else 'Nie'}`", False),
                    field("Pomysł na Event", f"```\n{kwargs.get('inputs', {}).get('field_5')}\n```", False),
                ],
                footer=EmbCFG.EVENT.footer
            ),
            EmbedType.HELP: lambda **kwargs: EmbedCreator(
                title=EmbCFG.HELP.title,
                description=EmbCFG.HELP.description,
                color=Colors.get(EmbCFG.HELP.color),
                fields=[
                    field("Nickname Minecraft", f">>> `{kwargs.get('inputs', {}).get('field_1')}`", False),
                    field("Szczegóły Zgłoszenia", f"```\n{kwargs.get('inputs', {}).get('field_2')}\n```", False),
                    field("Próby Rozwiązania", f"```\n{kwargs.get('inputs', {}).get('field_3')}\n```", False),
                ],
                footer=EmbCFG.HELP.footer
            ),
            EmbedType.CK: lambda **kwargs: EmbedCreator(
                title=EmbCFG.CK.title,
                description=EmbCFG.CK.description,
                color=Colors.get(EmbCFG.CK.color),
                fields=[
                    field("Nickname Minecraft", f">>> `{kwargs.get('inputs', {}).get('field_1')}`", False),
                    field("Oponent", f">>> {kwargs.get('inputs', {}).get('field_2').mention if hasattr(kwargs.get('inputs', {}).get('field_2'), 'mention') else '`' + str(kwargs.get('inputs', {}).get('field_2')) + '`'}", False),
                    field("Potrzebny GM", f">>> `{'Tak' if kwargs.get('inputs', {}).get('field_3') else 'Nie'}`", False),
                    field("Opis Śmierci", f"```\n{kwargs.get('inputs', {}).get('field_4')}\n```", False),
                ],
                footer=EmbCFG.CK.footer
            ),
            EmbedType.REPORT_PLAYER: lambda **kwargs: EmbedCreator(
                title=EmbCFG.REPORT_PLAYER.title,
                description=EmbCFG.REPORT_PLAYER.description,
                color=Colors.get(EmbCFG.REPORT_PLAYER.color),
                fields=[
                    field("Zgłaszany Gracz", f">>> {kwargs.get('inputs', {}).get('field_1').mention if hasattr(kwargs.get('inputs', {}).get('field_1'), 'mention') else '`' + str(kwargs.get('inputs', {}).get('field_1')) + '`'}", False),
                    field("Szczegóły Zgłoszenia", f"```\n{kwargs.get('inputs', {}).get('field_2')}\n```", False),
                ],
                footer=EmbCFG.REPORT_PLAYER.footer
            ),
            EmbedType.REPORT_ERROR: lambda **kwargs: EmbedCreator(
                title=EmbCFG.REPORT_ERROR.title,
                description=EmbCFG.REPORT_ERROR.description,
                color=Colors.get(EmbCFG.REPORT_ERROR.color),
                fields=[
                    field("Szczegóły Zgłoszenia", f"```\n{kwargs.get('inputs', {}).get('field_1')}\n```", False),
                ],
                footer=EmbCFG.REPORT_ERROR.footer
            ),
            EmbedType.CONTACT: lambda **kwargs: EmbedCreator(
                title=EmbCFG.CONTACT.title,
                description=EmbCFG.CONTACT.description,
                color=Colors.get(EmbCFG.CONTACT.color),
                fields=[
                    field("Temat", f">>> `{kwargs.get('inputs', {}).get('field_1')}`", False),
                    field("Treść", f"```\n{kwargs.get('inputs', {}).get('field_2')}\n```", False),
                ],
                footer=EmbCFG.CONTACT.footer
            ),
        }

    def get(self, embed_type: EmbedType, **kwargs):
        embed_factory = self.embeds.get(embed_type)
        if not embed_factory:
            return None
        return embed_factory(**kwargs)
