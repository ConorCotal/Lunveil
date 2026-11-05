import discord

from ..utils import check_owner
from ..UI import EmbedType
from ..logging_utils import log_action, logger
from ..threads import resolve_kp_thread_from_mention
from config.Manager import ConfigManager

config = ConfigManager()

class ManageHandler:
    def __init__(self, bot, handlers):
        self.bot = bot
        self.handlers = handlers

    async def kp_options(self, interaction: discord.Interaction):
        custom_id = interaction.data.get("custom_id")
        log_action("kp_type_selected", interaction, kp_type=custom_id)
        owner_id = await check_owner(self.handlers.repository, interaction)
        if owner_id is None:
            return

        await interaction.response.defer()
        await interaction.message.delete()

        parent_channel = interaction.guild.get_channel(config.KP.Channel_ID)
        if parent_channel is None:
            raise RuntimeError(f"KP parent channel not found: {config.KP.Channel_ID}")
        await parent_channel.set_permissions(interaction.user, send_messages_in_threads=True)

        if custom_id == "og_kp":
            await interaction.channel.send(
            embed=self.handlers.embed.get(EmbedType.OG_KP, template=config.KP.Template),
            view=self.handlers.buttons.kp_handling_view
        )
        elif custom_id == "transfer_kp":
            await interaction.channel.send(
            embed=self.handlers.embed.get(EmbedType.TRANSFER_KP),
            view=self.handlers.buttons.kp_handling_view
        )

    async def kp_handling(self, interaction: discord.Interaction):
        custom_id = interaction.data.get("custom_id")
        modal_values = interaction.data.get("modal_values", {})
        log_action("kp_workflow_action", interaction, workflow_action=custom_id)
        owner_id = await check_owner(self.handlers.repository, interaction)

        if owner_id is None:
            return

        if custom_id in ("done", "edit_done"):
            await interaction.response.send_modal(
                self.handlers.modals.confirm_kp_modal(source_message=interaction.message)
            )
            return
        if custom_id == "cancel":
            await interaction.response.send_modal(self.handlers.modals.cancel_kp_modal())
            return
            
        if custom_id == "cancel_confirmation":
            await interaction.response.defer()
            if not modal_values.get("cancel_confirmation"):
                await interaction.followup.send("Anulowanie KP nie zostało potwierdzone.", ephemeral=True)
                log_action("cancellation_not_confirmed", interaction)
                return

            thread_id = str(interaction.channel_id)
            await self.handlers.repository.remove(int(thread_id))

            await interaction.channel.delete()
            parent_channel = interaction.guild.get_channel(config.KP.Channel_ID)
            if parent_channel is None:
                raise RuntimeError(f"KP parent channel not found: {config.KP.Channel_ID}")
            await parent_channel.set_permissions(interaction.user, send_messages_in_threads=False)
            log_action("kp_cancelled", interaction, thread_id=thread_id, owner_id=owner_id)

    async def kp_confirmation(self, interaction: discord.Interaction):
        log_action("kp_submission_requested", interaction)
        owner_id = await check_owner(self.handlers.repository, interaction)
        if owner_id is None:
            return

        if not interaction.data.get("modal_values", {}).get("confirm_confirmation"):
            await interaction.response.send_message(
                "Wysłanie KP nie zostało potwierdzone.",
                ephemeral=True,
            )
            log_action("kp_submission_not_confirmed", interaction)
            return

        await interaction.response.defer(ephemeral=True)
        channel = interaction.channel
        messages_to_send = []

        async for message in channel.history(oldest_first=True, limit=100):
            if message.author.bot:
                continue

            if message.author.id != owner_id:
                continue

            content = message.content or None
            embeds = list(message.embeds) if message.embeds else None
            files = [await attachment.to_file() for attachment in message.attachments] if message.attachments else None

            if content or embeds or files:
                messages_to_send.append((message.created_at, content, embeds, files, message))

        if not messages_to_send:
            await interaction.followup.send("Nie znaleziono żadnych wiadomości użytkownika do przesłania.", ephemeral=True)
            logger.warning(
                "KP submission contained no user messages thread_id=%s user_id=%s",
                interaction.channel_id,
                owner_id,
            )
            return

        messages_to_send.sort(key=lambda item: item[0])

        username = interaction.user.global_name or interaction.user.name
        avatar_url = interaction.user.display_avatar.url

        webhook_channel = getattr(channel, "parent", None) or channel
        if not hasattr(webhook_channel, "create_webhook"):
            webhook_channel = channel
        if not hasattr(webhook_channel, "create_webhook"):
            raise RuntimeError(f"Cannot create a webhook for KP channel {interaction.channel_id}")

        thread_target = channel if isinstance(channel, discord.Thread) else None
        webhook = await webhook_channel.create_webhook(name=f"KP - {username}")
        try:
            for _, content, embeds, files, message in messages_to_send:
                send_kwargs = {
                    "username": username,
                    "avatar_url": avatar_url
                }
                if content is not None:
                    send_kwargs["content"] = content
                if embeds:
                    send_kwargs["embeds"] = embeds
                if files:
                    send_kwargs["files"] = files
                if thread_target is not None:
                    send_kwargs["thread"] = thread_target

                if send_kwargs.get("content") or send_kwargs.get("embeds") or send_kwargs.get("files"):
                    content = send_kwargs.get("content")
                    if content and len(content) > 2000:
                        for i in range(0, len(content), 2000):
                            chunk = content[i:i+2000]
                            chunk_kwargs = {k: v for k, v in send_kwargs.items() if k != "embeds"}
                            chunk_kwargs["content"] = chunk
                            if i == 0 and send_kwargs.get("embeds"):
                                chunk_kwargs["embeds"] = send_kwargs["embeds"]
                            await webhook.send(**chunk_kwargs)
                    else:
                        await webhook.send(**send_kwargs)
                else:
                    await webhook.send(username=username, avatar_url=avatar_url, thread=thread_target, content="(pusta wiadomość użytkownika)")

                await message.delete()
        finally:
            await webhook.delete()

        source_message = interaction.data.get("modal_source_message")
        if source_message is not None:
            await source_message.delete()
        await interaction.followup.send("Zakończyłeś tworzenie KP. Teraz musisz poczekać na zatwierdzenie przez rekrutera.", ephemeral=True)
        
        channel = interaction.guild.get_channel(interaction.channel_id)
        if channel:
            await channel.edit(locked=True)

        announce_channel = interaction.guild.get_channel(config.KP.Announce_ID)
        if announce_channel is None:
            raise RuntimeError(f"KP announce channel not found: {config.KP.Announce_ID}")
        await announce_channel.send(embed=self.handlers.embed.get(EmbedType.KP_TO_CONFIRM, thread=interaction.channel.mention, user=interaction.user.mention),
                                    view=self.handlers.buttons.kp_to_confirm_view)
        parent_channel = interaction.guild.get_channel(config.KP.Channel_ID)
        if parent_channel is None:
            raise RuntimeError(f"KP parent channel not found: {config.KP.Channel_ID}")
        await parent_channel.set_permissions(
            interaction.user,
            send_messages_in_threads=False,
        )
        log_action(
            "kp_thread_write_permission_revoked",
            interaction,
            thread_id=interaction.channel_id,
            owner_id=owner_id,
        )
        log_action(
            "kp_submitted_for_review",
            interaction,
            thread_id=interaction.channel_id,
            message_count=len(messages_to_send),
        )

    async def kp_to_confirm_handling(self, interaction: discord.Interaction):
        custom_id = interaction.data.get("custom_id")
        log_action("kp_review_decided", interaction, review_action=custom_id)
        if not interaction.message.embeds:
            await interaction.response.send_message("Wiadomość do akceptacji KP jest nieprawidłowa.", ephemeral=True)
            return
        await interaction.response.defer()
        emb = interaction.message.embeds[0]
        thread = await resolve_kp_thread_from_mention(interaction.guild, emb.description)
        if thread is None:
            await interaction.followup.send("Nie udało się znaleźć wątku KP do zamknięcia.", ephemeral=True)
            logger.error(
                "KP review message points to a missing thread reviewer_id=%s message_id=%s",
                interaction.user.id,
                interaction.message.id,
            )
            return

        if custom_id == "kp_to_confirm":
            await thread.send(embed=self.handlers.embed.get(EmbedType.KP_STATUS, status="Zatwierdzona"))
        elif custom_id == "kp_to_confirm_reject":
            await thread.send(embed=self.handlers.embed.get(EmbedType.KP_STATUS, status="Odrzucona"))

        await interaction.message.edit(
            embed=self.handlers.embed.get(
                EmbedType.KP_CONFIRMED,
                status="Zatwierdzona" if custom_id == "kp_to_confirm" else "Odrzucona",
                thread=thread.mention,
                user=interaction.user.mention
            ),
            view=None
        )

        try:
            await thread.edit(archived=True, locked=True)
        except discord.HTTPException:
            logger.exception("Failed to close reviewed KP thread thread_id=%s", thread.id)
        log_action(
            "kp_review_completed",
            interaction,
            thread_id=thread.id,
            status="approved" if custom_id == "kp_to_confirm" else "rejected",
        )
