import time
import discord
import asyncio

from ..UI import EmbedType
from ..logging_utils import log_action, logger
from config.Manager import ConfigManager

config = ConfigManager()

class CreateHandler:
    def __init__(self, bot, handlers):
        self.bot = bot
        self.handlers = handlers

    async def send_kp_panel(self, interaction: discord.Interaction):
        log_action("panel_sent", interaction)
        await interaction.response.send_message(config.KP.Messages.sending_panel, ephemeral=True)
        await interaction.channel.send(embed=self.handlers.embed.get(EmbedType.PANEL), view=self.handlers.buttons.create_kp_view)


    async def _clear_pending_kp(self, user_id: int, expires_at: float):
        await asyncio.sleep(max(0, expires_at - time.time()))
        if self.handlers.pending_kp_creations.get(user_id) == expires_at:
            self.handlers.pending_kp_creations.pop(user_id, None)

    async def set_kp_title(self, interaction: discord.Interaction):
        log_action("creation_started", interaction)
        cooldown = self.handlers.pending_kp_creations.get(interaction.user.id)
        now = time.time()
        if cooldown is not None:
            if cooldown > now:
                log_action("creation_blocked_by_pending_modal", interaction, expires_at=int(cooldown))
                await interaction.response.send_message(
                    f"Już otworzyłeś KP. Spróbuj ponownie <t:{int(cooldown)}:R>.",
                    ephemeral=True
                )
                return
            self.handlers.pending_kp_creations.pop(interaction.user.id, None)

        cooldown_time = now + 300
        self.handlers.pending_kp_creations[interaction.user.id] = cooldown_time
        asyncio.create_task(self._clear_pending_kp(interaction.user.id, cooldown_time))

        await interaction.response.send_modal(self.handlers.modals.set_kp_title_modal(interaction))

    async def create_kp_thread(self, interaction: discord.Interaction):
        log_action("creation_submitted", interaction)
        created_thread = None
        try:
            limit = 1
            kp_count = 0
            modal_values = interaction.data.get("modal_values", {})
            user_role_ids = {role.id for role in interaction.user.roles}

            for _thread_id, _owner_id in self.handlers.repository.records_for_owner(interaction.user.id):
                kp_count += 1

            for bypass_entry in getattr(config.KP, "Bypass_Roles", []):
                try:
                    bypass_role_id = int(getattr(bypass_entry, "role", bypass_entry))
                except (TypeError, ValueError):
                    continue

                if bypass_role_id not in user_role_ids:
                    continue

                bypass_limit = getattr(bypass_entry, "limit", None)
                try:
                    bypass_limit = int(bypass_limit) if bypass_limit is not None else 1
                except (TypeError, ValueError):
                    bypass_limit = 1

                limit = max(limit, bypass_limit)

            if limit < 999 and kp_count >= limit:
                log_action(
                    "creation_rejected_limit",
                    interaction,
                    current_count=kp_count,
                    limit=limit,
                )
                await interaction.response.send_message(
                    config.KP.Messages.kp_limit_reached.format(limit=limit),
                    ephemeral=True,
                )
                return

            await interaction.response.defer(ephemeral=True)
            parent_channel = interaction.guild.get_channel(config.KP.Channel_ID)
            if parent_channel is None:
                raise RuntimeError(f"KP parent channel not found: {config.KP.Channel_ID}")
            await parent_channel.set_permissions(
                interaction.user,
                send_messages_in_threads=False,
            )

            for thread_id, _owner_id in self.handlers.repository.records_for_owner(interaction.user.id):
                thread = interaction.guild.get_thread(thread_id) or interaction.guild.get_channel(thread_id)
                if thread is None:
                    logger.warning(
                        "KP thread missing while locking previous thread thread_id=%s user_id=%s",
                        thread_id,
                        interaction.user.id,
                    )
                    continue
                try:
                    await thread.edit(locked=True)
                except discord.HTTPException:
                    logger.exception(
                        "Failed to lock previous KP thread thread_id=%s user_id=%s",
                        thread_id,
                        interaction.user.id,
                    )

            if not isinstance(interaction.channel, discord.TextChannel):
                raise RuntimeError("KP creation must be started from a text channel")
            created_thread = await interaction.channel.create_thread(
                name=config.KP.Thread_Name.format(title=modal_values.get("set_kp_title")),
                type=discord.ChannelType.private_thread,
                invitable=False,
            )
            await created_thread.add_user(interaction.user)

            await self.handlers.repository.register(
                created_thread.id,
                interaction.user.id,
                created_thread.name,
            )

            await interaction.followup.send(
                embed=self.handlers.embed.get(EmbedType.KP_CREATED, thread=created_thread.jump_url),
                ephemeral=True,
            )
            await created_thread.send(
                embed=self.handlers.embed.get(EmbedType.KP_OPTIONS),
                view=self.handlers.buttons.kp_options_view,
            )
            mention = await created_thread.send(interaction.user.mention)
            await mention.delete()
            log_action("creation_completed", interaction, thread_id=created_thread.id)
        except Exception:
            if (
                created_thread is not None
                and self.handlers.repository.owner_for_thread(created_thread.id) is None
            ):
                try:
                    await created_thread.delete()
                except discord.HTTPException:
                    logger.exception(
                        "Failed to clean up unregistered KP thread thread_id=%s",
                        created_thread.id,
                    )
            raise
        finally:
            self.handlers.pending_kp_creations.pop(interaction.user.id, None)