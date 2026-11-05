from enum import Enum

from config.Manager import ConfigManager
from utils import EmbedCreator, field, Colors

config = ConfigManager()
EmbCFG = config.KP.Embeds

class EmbedType(Enum):
    PANEL = 1
    KP_CREATED = 2
    KP_OPTIONS = 3
    OG_KP = 4
    TRANSFER_KP = 5
    EDIT_ANNOUNCE = 6
    EDIT_DONE = 7
    EDIT_REJECTED = 8
    KP_TO_CONFIRM = 9
    KP_STATUS = 10
    KP_CONFIRMED = 11

class Embed:
    def __init__(self, bot):
        self.bot = bot

        self.embeds = {
            EmbedType.PANEL: lambda **kwargs: EmbedCreator(
                title=EmbCFG.PANEL.title,
                color=Colors.get(EmbCFG.PANEL.color),
            ),
            EmbedType.KP_CREATED: lambda **kwargs: EmbedCreator(
                title=EmbCFG.KP_CREATED.title,
                color=Colors.get(EmbCFG.KP_CREATED.color),
                fields=[
                    field(
                        name=field_cfg.name,
                        value=field_cfg.value.format(thread=kwargs.get("thread", "Brak linku")),
                        inline=getattr(field_cfg, "inline", False)
                    ) for field_cfg in EmbCFG.KP_CREATED.fields
                ]
            ),
            EmbedType.KP_OPTIONS: lambda **kwargs: EmbedCreator(
                title=EmbCFG.KP_OPTIONS.title,
                description=EmbCFG.KP_OPTIONS.description,
                color=Colors.get(EmbCFG.KP_OPTIONS.color),
                fields=[
                    field(
                        name=field_cfg.name,
                        value=field_cfg.value,
                        inline=getattr(field_cfg, "inline", False)
                    ) for field_cfg in EmbCFG.KP_OPTIONS.fields
                ]
            ),
            EmbedType.OG_KP: lambda **kwargs: EmbedCreator(
                title=EmbCFG.OG_KP.title,
                description=EmbCFG.OG_KP.description,
                color=Colors.get(EmbCFG.OG_KP.color),
                fields=[
                    field(
                        name=field_cfg.name,
                        value=field_cfg.value.format(template=kwargs.get("template", "Brak szablonu")),
                        inline=getattr(field_cfg, "inline", False)
                    ) for field_cfg in EmbCFG.OG_KP.fields
                ]
            ),
            EmbedType.TRANSFER_KP: lambda **kwargs: EmbedCreator(
                title=EmbCFG.TRANSFER_KP.title,
                description=EmbCFG.TRANSFER_KP.description,
                color=Colors.get(EmbCFG.TRANSFER_KP.color),
            ),
            EmbedType.EDIT_ANNOUNCE: lambda **kwargs: EmbedCreator(
                title=EmbCFG.EDIT_ANNOUNCE.title,
                description=EmbCFG.EDIT_ANNOUNCE.description.format(
                    user=kwargs.get("user", "Nieznany użytkownik"),
                    thread=kwargs.get("thread", "Brak linku")),
                color=Colors.get(EmbCFG.EDIT_ANNOUNCE.color),
                fields=[
                    field(
                        name=field_cfg.name,
                        value=field_cfg.value.format(reason=kwargs.get("reason", "Brak powodu")),
                        inline=getattr(field_cfg, "inline", False)
                    ) for field_cfg in EmbCFG.EDIT_ANNOUNCE.fields
                ]
            ),
            EmbedType.EDIT_DONE: lambda **kwargs: EmbedCreator(
                title=EmbCFG.EDIT_DONE.title.format(status=kwargs.get("status", "`NONE`")),
                description=EmbCFG.EDIT_DONE.description.format(
                    user=kwargs.get("user", "Nieznany użytkownik"),
                    thread=kwargs.get("thread", "Brak linku")),
                color=Colors.get(EmbCFG.EDIT_DONE.color),
            ),
            EmbedType.EDIT_REJECTED: lambda **kwargs: EmbedCreator(
                title=EmbCFG.EDIT_REJECTED.title,
                description=EmbCFG.EDIT_REJECTED.description.format(thread=kwargs.get("thread", "Brak linku")),
                color=Colors.get(EmbCFG.EDIT_REJECTED.color),
                fields=[
                    field(
                        name=field_cfg.name,
                        value=field_cfg.value.format(reason=kwargs.get("reason", "Brak powodu")),
                        inline=getattr(field_cfg, "inline", False)
                    ) for field_cfg in EmbCFG.EDIT_REJECTED.fields
                ]
            ),
            EmbedType.KP_TO_CONFIRM: lambda **kwargs: EmbedCreator(
                title=EmbCFG.KP_TO_CONFIRM.title,
                description=EmbCFG.KP_TO_CONFIRM.description.format(thread=kwargs.get("thread", "Brak linku"), user=kwargs.get("user", "Nieznany użytkownik")),
                color=Colors.get(EmbCFG.KP_TO_CONFIRM.color),
            ),
            EmbedType.KP_STATUS: lambda **kwargs: EmbedCreator(
                title=EmbCFG.KP_STATUS.title.format(status=kwargs.get("status", "`NONE`")),
                color=Colors.get(EmbCFG.KP_STATUS.color),
            ),
            EmbedType.KP_CONFIRMED: lambda **kwargs: EmbedCreator(
                title=EmbCFG.KP_CONFIRMED.title.format(status=kwargs.get("status", "`NONE`")),
                description=EmbCFG.KP_CONFIRMED.description.format(user=kwargs.get("user", "Nieznany użytkownik"), thread=kwargs.get("thread", "Brak linku")),
                color=Colors.get(EmbCFG.KP_CONFIRMED.color),
            ),
        }

    def get(self, embed_type: EmbedType, **kwargs):
        embed_factory = self.embeds.get(embed_type)
        if not embed_factory:
            return None
        
        return embed_factory(**kwargs)