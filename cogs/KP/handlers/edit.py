import discord

from ..UI import EmbedType
from ..logging_utils import log_action, logger
from ..threads import resolve_kp_thread, thread_id_from_mention
from config.Manager import ConfigManager

config = ConfigManager()

class EditHandler:
    def __init__(self, bot, handlers):
        self.bot = bot
        self.handlers = handlers

    async def edit_kp_thread(self, interaction: discord.Interaction):
        custom_id = interaction.data.get("custom_id")

        if custom_id == "edit_kp":
            log_action("edit_started", interaction)
            modal_build_started = discord.utils.utcnow()
            modal = self.handlers.modals.edit_kp_modal(interaction)
            modal_build_ms = round(
                (discord.utils.utcnow() - modal_build_started).total_seconds() * 1000
            )
            log_action("edit_modal_built", interaction, build_ms=modal_build_ms)
            if modal is None:
                log_action("edit_unavailable_no_kp", interaction)
                await interaction.response.send_message(config.KP.Messages.dont_have_kp, ephemeral=True)
                return
            log_action("edit_modal_response_started", interaction, build_ms=modal_build_ms)
            await interaction.response.send_modal(modal)
            log_action("edit_modal_sent", interaction, build_ms=modal_build_ms)

        if custom_id == "edit_kp_modal":
            log_action("edit_requested", interaction)
            modal_values = interaction.data.get("modal_values", {})
            thread_id = modal_values.get("editKPmodal_select")
            if isinstance(thread_id, (list, tuple)):
                thread_id = thread_id[0] if thread_id else None
            reason = modal_values.get("editKPmodal_reason")
            if thread_id is None:
                await interaction.response.send_message("Nie wybrano KP do edycji.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            thread = await resolve_kp_thread(interaction.guild, int(thread_id))
            if thread is None:
                logger.warning(
                    "Selected KP thread no longer exists thread_id=%s user_id=%s",
                    thread_id,
                    interaction.user.id,
                )
                await interaction.followup.send("Nie znaleziono wybranego wątku.", ephemeral=True)
                return
            announce_channel = interaction.guild.get_channel(config.KP.Announce_ID)
            if announce_channel is None:
                raise RuntimeError(f"KP announce channel not found: {config.KP.Announce_ID}")

            await announce_channel.send(
                embed=self.handlers.embed.get(
                    EmbedType.EDIT_ANNOUNCE,
                    user=interaction.user.mention,
                    thread=thread.mention,
                    reason=reason,
                ),
                view=self.handlers.buttons.edit_request_view,
            )
            await interaction.followup.send(config.KP.Messages.edit_kp_requested, ephemeral=True)
            log_action("edit_request_announced", interaction, thread_id=thread.id)

    async def edit_request_handling(self, interaction: discord.Interaction):
        custom_id = interaction.data.get("custom_id")
        log_action("edit_request_reviewed", interaction, review_action=custom_id)
        if not interaction.message.embeds:
            await interaction.response.send_message("Wiadomość z prośbą o edycję jest nieprawidłowa.", ephemeral=True)
            return
        emb = interaction.message.embeds[0]
        thread_id = thread_id_from_mention(emb.description)
        if thread_id is None:
            await interaction.response.send_message("Nie udało się znaleźć wątku z prośby o edycję.", ephemeral=True)
            return
        
        user_id = self.handlers.repository.owner_for_thread(thread_id)

        if user_id is None:
            await interaction.response.send_message("Nie udało się znaleźć właściciela tej KP w bazie.", ephemeral=True)
            return

        if custom_id == "edit_cancel":
            await interaction.response.send_modal(
                self.handlers.modals.edit_rejected_modal(source_message=interaction.message)
            )
            log_action("edit_rejection_reason_requested", interaction, thread_id=thread_id, owner_id=user_id)
            return

        if custom_id == "edit_confirm":
            await interaction.response.defer()
            thread = await resolve_kp_thread(interaction.guild, thread_id)
            if thread is None:
                await interaction.followup.send(
                    "Nie udało się znaleźć wątku z prośby o edycję.",
                    ephemeral=True,
                )
                return

            owner = interaction.guild.get_member(int(user_id))
            if owner is None:
                owner = await interaction.guild.fetch_member(int(user_id))
            for other_thread_id, _owner_id in self.handlers.repository.records_for_owner(int(user_id)):
                if thread.id != other_thread_id:
                    other_thread = await resolve_kp_thread(interaction.guild, other_thread_id)
                    if other_thread is not None:
                        try:
                            await other_thread.edit(locked=True)
                        except discord.HTTPException:
                            logger.exception(
                                "Failed to lock previous KP thread thread_id=%s user_id=%s",
                                other_thread_id,
                                user_id,
                            )

            async for message in thread.history(limit=1, oldest_first=True):
                if message.embeds:
                    embed = message.embeds[0]
                    parent_channel = interaction.guild.get_channel(config.KP.Channel_ID)
                    if parent_channel is None:
                        raise RuntimeError(f"KP parent channel not found: {config.KP.Channel_ID}")
                    await parent_channel.set_permissions(
                        owner,
                        send_messages_in_threads=embed.title != config.KP.Embeds.KP_OPTIONS.title,
                    )
                    break

            if thread.archived:
                await thread.edit(archived=False)
            if thread.locked:
                await thread.edit(locked=False)
            mention = await thread.send(owner.mention)
            await mention.delete()
            await thread.send(" ", view=self.handlers.buttons.kp_edit_done_view)
            await interaction.message.edit(
                embed=self.handlers.embed.get(
                    EmbedType.EDIT_DONE,
                    user=interaction.user.mention,
                    thread=thread.mention,
                    status="zatwierdzona",
                ),
                view=None,
            )
            log_action("edit_approved", interaction, thread_id=thread.id, owner_id=user_id)

    async def handle_edit_rejection(self, interaction: discord.Interaction):
        custom_id = interaction.data.get("custom_id")

        if custom_id == "edit_rejected_modal":
            log_action("edit_rejection_submitted", interaction)
            await interaction.response.defer()
            modal_values = interaction.data.get("modal_values", {})
            reason = modal_values.get("editRejectedReason")

            # Pobierz wątek z prośby o edycję
            source_message = interaction.data.get("modal_source_message")
            if source_message is None or not source_message.embeds:
                await interaction.followup.send("Wiadomość z prośbą o edycję jest nieprawidłowa.", ephemeral=True)
                return
            emb = source_message.embeds[0]
            thread = await resolve_kp_thread_from_mention(interaction.guild, emb.description)

            if thread is None:
                await interaction.followup.send("Nie udało się znaleźć wątku z prośby o edycję.", ephemeral=True)
                return
            
            # Pobierz właściciela KP z bazy danych
            user_id = self.handlers.repository.owner_for_thread(thread.id)

            if user_id is None:
                await interaction.followup.send("Nie udało się znaleźć właściciela tej KP w bazie.", ephemeral=True)
                return

            owner = interaction.guild.get_member(int(user_id))
            if owner is None:
                owner = await interaction.guild.fetch_member(int(user_id))
            await owner.send(embed=self.handlers.embed.get(EmbedType.EDIT_REJECTED, reason=reason, thread=thread.mention))

            if source_message is not None:
                await source_message.edit(
                    embed=self.handlers.embed.get(
                        EmbedType.EDIT_DONE,
                        user=interaction.user.mention,
                        thread=thread.mention,
                        status="odrzucona",
                    ),
                    view=None,
                )
            log_action("edit_rejected", interaction, thread_id=thread.id, owner_id=user_id)