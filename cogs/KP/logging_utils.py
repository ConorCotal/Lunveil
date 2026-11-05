import logging
import os
import uuid

import discord


logger = logging.getLogger("bot.kp")
instance_id = uuid.uuid4().hex[:8]


def log_action(action: str, interaction: discord.Interaction, **details) -> None:
    data = interaction.data or {}
    context = {
        "action": action,
        "user_id": getattr(interaction.user, "id", None),
        "guild_id": interaction.guild_id,
        "channel_id": interaction.channel_id,
        "interaction_id": interaction.id,
        "interaction_age_ms": round(
            (discord.utils.utcnow() - interaction.created_at).total_seconds() * 1000
        ),
        "process_id": os.getpid(),
        "instance_id": instance_id,
        "custom_id": data.get("custom_id"),
    }
    context.update(details)
    logger.info(
        "KP action %s",
        " ".join(f"{key}={value!r}" for key, value in context.items()),
    )


async def report_interaction_error(
    interaction: discord.Interaction,
    action: str,
    error: Exception,
) -> None:
    data = interaction.data or {}
    if isinstance(error, discord.NotFound) and error.code == 10062:
        logger.warning(
            "KP interaction is unknown to Discord; it may have expired or been acknowledged "
            "by another bot instance action=%r user_id=%s guild_id=%s channel_id=%s "
            "interaction_id=%s interaction_age_ms=%s process_id=%s instance_id=%s "
            "custom_id=%r",
            action,
            getattr(interaction.user, "id", None),
            interaction.guild_id,
            interaction.channel_id,
            interaction.id,
            round((discord.utils.utcnow() - interaction.created_at).total_seconds() * 1000),
            os.getpid(),
            instance_id,
            data.get("custom_id"),
            exc_info=(type(error), error, error.__traceback__),
        )
        return

    logger.error(
        "KP action failed action=%r user_id=%s guild_id=%s channel_id=%s "
        "interaction_id=%s interaction_age_ms=%s process_id=%s instance_id=%s custom_id=%r",
        action,
        getattr(interaction.user, "id", None),
        interaction.guild_id,
        interaction.channel_id,
        interaction.id,
        round((discord.utils.utcnow() - interaction.created_at).total_seconds() * 1000),
        os.getpid(),
        instance_id,
        data.get("custom_id"),
        exc_info=(type(error), error, error.__traceback__),
    )

    try:
        if interaction.response.is_done():
            await interaction.followup.send(
                "Wystąpił błąd podczas obsługi tej akcji. Zapisano szczegóły do logu.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Wystąpił błąd podczas obsługi tej akcji. Zapisano szczegóły do logu.",
                ephemeral=True,
            )
    except discord.HTTPException:
        logger.exception(
            "Could not send KP error response interaction_id=%s",
            interaction.id,
        )
