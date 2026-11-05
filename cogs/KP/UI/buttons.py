import discord
from utils import ButtonCreator, button, get_button_style
from config.Manager import ConfigManager
from ..logging_utils import log_action, report_interaction_error

config = ConfigManager()
BtnCFG = config.KP.Buttons


class Buttons:
    def __init__(self, bot, handlers):
        self.bot = bot
        self.handlers = handlers
        self._in_flight_interactions = set()
        self.handler_map = {
            "create_kp": self.handlers.create.set_kp_title,
            "edit_kp": self.handlers.edit.edit_kp_thread,
            "og_kp": self.handlers.manage.kp_options,
            "transfer_kp": self.handlers.manage.kp_options,
            "edit_done": self.handlers.manage.kp_handling,
            "done": self.handlers.manage.kp_handling,
            "cancel": self.handlers.manage.kp_handling,
            "edit_confirm": self.handlers.edit.edit_request_handling,
            "edit_cancel": self.handlers.edit.edit_request_handling,
            "kp_to_confirm": self.handlers.manage.kp_to_confirm_handling,
            "kp_to_confirm_reject": self.handlers.manage.kp_to_confirm_handling
        }
        self.create()

    def create(self):
        self.create_kp_view = ButtonCreator(
            button(label=BtnCFG.CREATE_KP.label,
                   style=get_button_style(BtnCFG.CREATE_KP.style),
                   emoji=BtnCFG.CREATE_KP.emote if BtnCFG.CREATE_KP.emote != "" else None,
                   disabled=not BtnCFG.CREATE_KP.enabled,
                   custom_id="create_kp"),
            button(label=BtnCFG.EDIT_KP.label,
                   style=get_button_style(BtnCFG.EDIT_KP.style),
                   emoji=BtnCFG.EDIT_KP.emote if BtnCFG.EDIT_KP.emote != "" else None,
                   disabled=not BtnCFG.EDIT_KP.enabled,
                   custom_id="edit_kp"),
            callback=self.callback,
            persistent=True,
            bot=self.bot
        )

        self.kp_options_view = ButtonCreator(
            button(label=BtnCFG.KP_CREATOR.label,
                   style=get_button_style(BtnCFG.KP_CREATOR.style),
                   emoji=BtnCFG.KP_CREATOR.emote if BtnCFG.KP_CREATOR.emote != "" else None,
                   disabled=not BtnCFG.KP_CREATOR.enabled,
                   custom_id="kp_creator"),
            button(label=BtnCFG.OG_KP.label,
                   style=get_button_style(BtnCFG.OG_KP.style),
                   emoji=BtnCFG.OG_KP.emote if BtnCFG.OG_KP.emote != "" else None,
                   disabled=not BtnCFG.OG_KP.enabled,
                   custom_id="og_kp"),
            button(label=BtnCFG.TRANSFER_KP.label,
                   style=get_button_style(BtnCFG.TRANSFER_KP.style),
                   emoji=BtnCFG.TRANSFER_KP.emote if BtnCFG.TRANSFER_KP.emote != "" else None,
                   disabled=not BtnCFG.TRANSFER_KP.enabled,
                   custom_id="transfer_kp"),
            callback=self.callback,
            persistent=True,
            bot=self.bot
        )

        self.kp_handling_view = ButtonCreator(
            button(label=BtnCFG.DONE.label,
                   style=get_button_style(BtnCFG.DONE.style),
                   emoji=BtnCFG.DONE.emote if BtnCFG.DONE.emote != "" else None,
                   disabled=not BtnCFG.DONE.enabled,
                   custom_id="done"),
            button(label=BtnCFG.CANCEL.label,
                   style=get_button_style(BtnCFG.CANCEL.style),
                   emoji=BtnCFG.CANCEL.emote if BtnCFG.CANCEL.emote != "" else None,
                   disabled=not BtnCFG.CANCEL.enabled,
                   custom_id="cancel"),
            callback=self.callback,
            persistent=True,
            bot=self.bot
        )

        self.edit_request_view = ButtonCreator(
            button(label=BtnCFG.EDIT_CONFIRM.label,
                   style=get_button_style(BtnCFG.EDIT_CONFIRM.style),
                   emoji=BtnCFG.EDIT_CONFIRM.emote if BtnCFG.EDIT_CONFIRM.emote != "" else None,
                   disabled=not BtnCFG.EDIT_CONFIRM.enabled,
                   custom_id="edit_confirm"),
            button(label=BtnCFG.EDIT_CANCEL.label,
                   style=get_button_style(BtnCFG.EDIT_CANCEL.style),
                   emoji=BtnCFG.EDIT_CANCEL.emote if BtnCFG.EDIT_CANCEL.emote != "" else None,
                   disabled=not BtnCFG.EDIT_CANCEL.enabled,
                   custom_id="edit_cancel"),
            callback=self.callback,
            persistent=True,
            bot=self.bot
        )

        self.kp_to_confirm_view = ButtonCreator(
            button(label=BtnCFG.KP_TO_CONFIRM.label,
                   style=get_button_style(BtnCFG.KP_TO_CONFIRM.style),
                   emoji=BtnCFG.KP_TO_CONFIRM.emote if BtnCFG.KP_TO_CONFIRM.emote != "" else None,
                   disabled=not BtnCFG.KP_TO_CONFIRM.enabled,
                   custom_id="kp_to_confirm"),
            button(label=BtnCFG.KP_TO_CONFIRM_REJECT.label,
                   style=get_button_style(BtnCFG.KP_TO_CONFIRM_REJECT.style),
                   emoji=BtnCFG.KP_TO_CONFIRM_REJECT.emote if BtnCFG.KP_TO_CONFIRM_REJECT.emote != "" else None,
                   disabled=not BtnCFG.KP_TO_CONFIRM_REJECT.enabled,
                   custom_id="kp_to_confirm_reject"),
            callback=self.callback,
            persistent=True,
            bot=self.bot
        )

        self.kp_edit_done_view = ButtonCreator(
            button(label=BtnCFG.EDIT_DONE.label,
                   style=get_button_style(BtnCFG.EDIT_DONE.style),
                   emoji=BtnCFG.EDIT_DONE.emote if BtnCFG.EDIT_DONE.emote != "" else None,
                   disabled=not BtnCFG.EDIT_DONE.enabled,
                   custom_id="edit_done"),
            callback=self.callback,
            persistent=True,
            bot=self.bot
        )

    async def callback(self, interaction: discord.Interaction, btn: button):
        if interaction.id in self._in_flight_interactions:
            log_action("duplicate_button_dispatch_ignored", interaction)
            return

        self._in_flight_interactions.add(interaction.id)
        log_action("button_received", interaction, button_custom_id=btn.custom_id)
        try:
            handler = self.handler_map.get(btn.custom_id)
            if handler:
                if hasattr(handler, "to_dict"):
                    await interaction.response.send_modal(handler)
                else:
                    result = handler(interaction)
                    if hasattr(result, "__await__"):
                        await result
            else:
                await interaction.response.send_message("Nieznany przycisk.", ephemeral=True)

        except Exception as e:
            await report_interaction_error(interaction, "button_callback", e)
        finally:
            self._in_flight_interactions.discard(interaction.id)
