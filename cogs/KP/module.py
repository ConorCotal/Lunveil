import discord
import logging
import asyncio
from pathlib import Path
from discord.ext import commands
from discord import app_commands

from config.Manager import ConfigManager
from .handlers import Handlers
from .logging_utils import log_action, report_interaction_error
from .repository import KPRepository
from .threads import resolve_kp_thread

config = ConfigManager()
logger = logging.getLogger("bot.kp")


async def is_kp_staff(interaction: discord.Interaction) -> bool:
    user = interaction.user
    permissions = getattr(user, "guild_permissions", None)
    return bool(permissions and permissions.administrator) or any(
        role.id == config.KP.Recruiter_Role for role in getattr(user, "roles", [])
    )


class KPModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        database_path = Path(__file__).with_name("database.json")
        self.repository = KPRepository(str(database_path))
        logger.info(
            "KP repository initialized path=%s records=%s",
            self.repository.file_path,
            len(self.repository.records()),
        )
        self.handlers = Handlers(bot, self.repository)
        self._name_backfill_task = None

    @commands.Cog.listener()
    async def on_ready(self):
        if self._name_backfill_task is None or self._name_backfill_task.done():
            self._name_backfill_task = asyncio.create_task(self._backfill_thread_names())

    async def _backfill_thread_names(self):
        parent_channel = self.bot.get_channel(config.KP.Channel_ID)
        if not isinstance(parent_channel, discord.TextChannel):
            logger.error(
                "Cannot backfill KP thread names; parent channel unavailable channel_id=%s",
                config.KP.Channel_ID,
            )
            return

        for thread_id, _owner_id in self.repository.records():
            if self.repository.thread_name_for(thread_id):
                continue
            try:
                thread = await resolve_kp_thread(parent_channel.guild, thread_id)
                if thread is not None:
                    await self.repository.set_thread_name(thread_id, thread.name)
                    logger.info("Backfilled KP thread name thread_id=%s", thread_id)
            except (discord.HTTPException, KeyError):
                logger.exception("Failed to backfill KP thread name thread_id=%s", thread_id)

    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(
        name="kp-panel",
        description="Wysyła panel tworzenia KP."
    )
    async def kp_panel(self, interaction: discord.Interaction):
        log_action("panel_command", interaction)
        await self.handlers.create.send_kp_panel(interaction)

    @kp_panel.error
    async def kp_panel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            logger.warning(
                "KP panel permission denied user_id=%s guild_id=%s",
                getattr(interaction.user, "id", None),
                interaction.guild_id,
            )
            message = "Tylko administrator może wysłać panel KP."
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
            return

        await report_interaction_error(interaction, "kp_panel_command", error)

    @app_commands.command(
        name="kp-search",
        description="Wyszukuje wątki KP należące do użytkownika.",
    )
    @app_commands.describe(user="Użytkownik, którego KP chcesz znaleźć")
    @app_commands.check(is_kp_staff)
    async def kp_search(self, interaction: discord.Interaction, user: discord.Member):
        log_action("search_started", interaction, target_user_id=user.id)
        await interaction.response.defer(ephemeral=True)
        matches = []
        unavailable = 0

        for resolved_thread_id, owner_id in self.repository.records_for_owner(user.id):

            try:
                thread = await resolve_kp_thread(interaction.guild, resolved_thread_id)
            except discord.HTTPException:
                unavailable += 1
                continue
            if thread is None:
                unavailable += 1
                continue

            if not isinstance(thread, discord.Thread):
                logger.warning(
                    "KP search record does not refer to a thread thread_id=%s",
                    resolved_thread_id,
                )
                continue

            status = "zamknięta" if thread.locked else "zarchiwizowana" if thread.archived else "otwarta"
            matches.append(f"• [{thread.name}]({thread.jump_url}) — {status}")

        log_action(
            "search_completed",
            interaction,
            target_user_id=user.id,
            result_count=len(matches),
            unavailable_count=unavailable,
        )

        if not matches:
            message = f"Nie znaleziono dostępnych KP użytkownika {user.mention}."
            if unavailable:
                message += f" Nie udało się sprawdzić {unavailable} zapisanych wątków."
            await interaction.followup.send(message, ephemeral=True)
            return

        header = f"KP użytkownika {user.mention}:\n"
        shown_matches = []
        for match in matches:
            candidate = "\n".join([*shown_matches, match])
            if len(header) + len(candidate) > 1700:
                break
            shown_matches.append(match)
        message = header + "\n".join(shown_matches)
        if len(matches) > len(shown_matches):
            message += f"\n…oraz {len(matches) - len(shown_matches)} kolejnych."
        if unavailable:
            message += f"\nNie udało się sprawdzić {unavailable} zapisanych wątków."
        await interaction.followup.send(message, ephemeral=True)

    @kp_search.error
    async def kp_search_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            logger.warning(
                "KP search permission denied user_id=%s guild_id=%s",
                getattr(interaction.user, "id", None),
                interaction.guild_id,
            )
            message = "Tę komendę może użyć tylko rekruter lub administrator."
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
            return

        logger.error(
            "KP search command failed user_id=%s guild_id=%s",
            getattr(interaction.user, "id", None),
            interaction.guild_id,
            exc_info=(type(error), error, error.__traceback__),
        )
        message = "Wyszukiwanie KP nie powiodło się. Szczegóły zapisano w logu."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread):
        if thread.parent_id != config.KP.Channel_ID:
            return

        if await self.repository.remove(thread.id):
            logger.info(
                "KP thread deleted and database record removed thread_id=%s",
                thread.id,
            )

async def setup(bot):
    cog = KPModule(bot)
    await cog.repository.migrate_legacy_records()
    await bot.add_cog(cog)