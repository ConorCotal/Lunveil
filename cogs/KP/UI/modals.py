import discord
import logging
from utils import ModalCreator, ModalInput, ModalInputType
from config.Manager import ConfigManager
from ..logging_utils import log_action, report_interaction_error

config = ConfigManager()
ModCFG = config.KP.Modals
logger = logging.getLogger("bot.kp")

class Modals:
    def __init__(self, bot, handlers):
        self.bot = bot
        self.handlers = handlers
        self.handler_map = {
            "cancel_confirmation": self.handlers.manage.kp_handling,
            "confirm_confirmation": self.handlers.manage.kp_confirmation,
            "set_kp_title": self.handlers.create.create_kp_thread,
            "edit_kp_modal": self.handlers.edit.edit_kp_thread,
            "edit_rejected_modal": self.handlers.edit.handle_edit_rejection
        }

    def set_kp_title_modal(self, interaction: discord.Interaction):
        return ModalCreator(
            title=ModCFG.SET_KP_TITLE.title,
            action_id="set_kp_title",
            inputs=[
                ModalInput(
                    type=ModalInputType.TEXT,
                    label=ModCFG.SET_KP_TITLE.label,
                    default=ModCFG.SET_KP_TITLE.default.format(user=interaction.user.global_name),
                    custom_id="set_kp_title",
                    rquired=True
                )
            ],
            callback=self.callback,
            timeout=None
        )

    def cancel_kp_modal(self):
        return ModalCreator(
            title=ModCFG.CANCEL_CONFIRMATION.title,
            action_id="cancel_confirmation",
            inputs=[
                ModalInput(
                    type=ModalInputType.CHECKBOX,
                    label=ModCFG.CANCEL_CONFIRMATION.label,
                    custom_id="cancel_confirmation"
                )
            ],
            callback=self.callback,
            timeout=None
        )
    
    def confirm_kp_modal(self, source_message=None):
        return ModalCreator(
            title=ModCFG.CONFIRM_CONFIRMATION.title,
            action_id="confirm_confirmation",
            inputs=[
                ModalInput(
                    type=ModalInputType.CHECKBOX,
                    label=ModCFG.CONFIRM_CONFIRMATION.label,
                    custom_id="confirm_confirmation"
                )
            ],
            callback=lambda interaction, data: self.callback(
                interaction,
                data,
                source_message=source_message,
            ),
            timeout=None
        )
    
    def edit_kp_modal(self, interaction: discord.Interaction):
        options = []
        owned_records = 0
        for thread_id, _owner_id in self.handlers.repository.records_for_owner(interaction.user.id):
            owned_records += 1

            thread = interaction.guild.get_thread(thread_id) or interaction.guild.get_channel(thread_id)
            label = (
                thread.name
                if isinstance(thread, discord.Thread)
                else self.handlers.repository.thread_name_for(thread_id) or f"KP {thread_id}"
            )
            if thread is None:
                logger.info(
                    "KP thread not cached; presenting ID as edit option thread_id=%s user_id=%s",
                    thread_id,
                    interaction.user.id,
                )

            options.append(
                discord.SelectOption(
                    label=label[:100],
                    value=str(thread_id)
                )
            )

        logger.info(
            "KP edit options resolved user_id=%s registered_records=%s available_threads=%s",
            interaction.user.id,
            owned_records,
            len(options),
        )
        if not options:
            return None

        if len(options) > 25:
            logger.warning(
                "User has more KP threads than a Discord select can display; truncating options "
                "user_id=%s total=%s",
                interaction.user.id,
                len(options),
            )
            options = options[:25]

        return ModalCreator(
            title=ModCFG.EDIT_KP.title,
            action_id="edit_kp_modal",
            inputs=[
                ModalInput(
                    type=ModalInputType.SELECT,
                    label=ModCFG.EDIT_KP.inputs[0].input.label,
                    custom_id="editKPmodal_select",
                    required=True,
                    options=options
                ),
                ModalInput(
                    type=ModalInputType.TEXT,
                    label=ModCFG.EDIT_KP.inputs[1].input.label,
                    placeholder=ModCFG.EDIT_KP.inputs[1].input.placeholder,
                    custom_id="editKPmodal_reason",
                    rquired=True
                )
            ],
            callback=self.callback,
            timeout=None
        )
    
    def edit_rejected_modal(self, source_message=None):
        return ModalCreator(
            title=ModCFG.EDIT_REJECTED.title,
            action_id="edit_rejected_modal",
            inputs=[
                ModalInput(
                    type=ModalInputType.TEXT,
                    label=ModCFG.EDIT_REJECTED.inputs[0].input.label,
                    placeholder=ModCFG.EDIT_REJECTED.inputs[0].input.placeholder,
                    custom_id="editRejectedReason",
                    rquired=True
                )
            ],
            callback=lambda interaction, data: self.callback(
                interaction,
                data,
                source_message=source_message,
            ),
            timeout=None
        )

    async def callback(self, interaction: discord.Interaction, data, source_message=None):
        log_action("modal_submitted", interaction)
        try:
            action_id = (interaction.data or {}).get("custom_id")
            handler = self.handler_map.get(action_id)

            if handler:
                interaction.data["modal_values"] = data
                if source_message is not None:
                    interaction.data["modal_source_message"] = source_message
                result = handler(interaction)
                if hasattr(result, "__await__"):
                    await result
            else:
                logger.error(
                    "No KP modal handler registered action_id=%r interaction_id=%s",
                    action_id,
                    interaction.id,
                )
                await interaction.response.send_message("Błąd systemu: Brak zarejestrowanego handlera dla tej akcji.", ephemeral=True)

        except Exception as e:
            await report_interaction_error(interaction, "modal_callback", e)