import re
import discord
from typing import Optional

from config.Manager import ConfigManager
from .logging_utils import log_action


config = ConfigManager()

async def check_owner(self, interaction: discord.Interaction) -> Optional[int]:
    owner_id = self.owner_for_thread(interaction.channel_id)

    if owner_id is None:
        log_action(
            "authorization_denied_unregistered_thread",
            interaction,
            channel_object_id=getattr(interaction.channel, "id", None),
            repository_path=self.file_path,
            repository_records=len(self.records()),
        )
        message = config.KP.Messages.thread_not_registered
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
        return None

    if interaction.user.id != owner_id:
        log_action("authorization_denied_not_owner", interaction, owner_id=owner_id)
        message = config.KP.Messages.not_owner
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
        return None

    return owner_id


def channel_from_mention(mention: str, guild: discord.Guild) -> Optional[discord.abc.GuildChannel]:
    if not mention:
        return None

    patterns = [
        r"<#(\d+)>",
        r"https?://(?:canary\.)?discord(?:app)?\.com/channels/\d+/(\d+)(?:/\d+)?",
    ]

    channel_id = None
    for pattern in patterns:
        m = re.search(pattern, mention)
        if m:
            channel_id = int(m.group(1))
            break

    if channel_id is None:
        return None

    channel = guild.get_channel(channel_id)
    if channel is not None:
        return channel

    if hasattr(guild, "get_thread"):
        return guild.get_thread(channel_id)

    return None