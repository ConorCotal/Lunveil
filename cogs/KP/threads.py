import re

import discord

from .logging_utils import logger


def thread_id_from_mention(mention: str | None) -> int | None:
    if not mention:
        return None

    patterns = (
        r"<#(\d+)>",
        r"https?://(?:canary\.)?discord(?:app)?\.com/channels/\d+/(\d+)(?:/\d+)?",
    )
    for pattern in patterns:
        match = re.search(pattern, mention)
        if match:
            return int(match.group(1))
    return None


async def resolve_kp_thread(guild: discord.Guild, thread_id: int) -> discord.Thread | None:
    channel = guild.get_thread(thread_id) or guild.get_channel(thread_id)
    if isinstance(channel, discord.Thread):
        return channel

    try:
        channel = await guild.fetch_channel(thread_id)
    except discord.NotFound:
        channel = None
    except discord.Forbidden:
        logger.warning("Bot cannot fetch KP thread thread_id=%s", thread_id)
        channel = None
    except discord.HTTPException:
        logger.exception("Failed to fetch KP thread thread_id=%s", thread_id)
        raise

    if isinstance(channel, discord.Thread):
        return channel

    from config.Manager import ConfigManager

    parent = guild.get_channel(ConfigManager().KP.Channel_ID)
    if not isinstance(parent, discord.TextChannel):
        logger.warning("KP parent channel unavailable while resolving thread_id=%s", thread_id)
        return None

    for joined in (True, False):
        try:
            async for archived_thread in parent.archived_threads(
                private=True,
                joined=joined,
                limit=None,
            ):
                if archived_thread.id == thread_id:
                    return archived_thread
        except discord.Forbidden:
            if joined:
                logger.info(
                    "Cannot list joined private KP threads thread_id=%s; trying moderator access",
                    thread_id,
                )
                continue
            logger.warning("Bot cannot list archived private KP threads thread_id=%s", thread_id)
            return None
        except discord.HTTPException:
            logger.exception("Failed to list archived private KP threads thread_id=%s", thread_id)
            raise

    logger.warning("KP thread could not be resolved from cache, API, or archives thread_id=%s", thread_id)
    return None


async def resolve_kp_thread_from_mention(
    guild: discord.Guild,
    mention: str | None,
) -> discord.Thread | None:
    thread_id = thread_id_from_mention(mention)
    if thread_id is None:
        return None
    return await resolve_kp_thread(guild, thread_id)
