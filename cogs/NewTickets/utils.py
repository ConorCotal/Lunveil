import re
import discord
from typing import Optional

from config.Manager import ConfigManager

config = ConfigManager()

async def check_owner(self, interaction: discord.Interaction) -> Optional[int]:
    owner_id = None

    for db_key, db_value in self.items():
        if db_key == str(interaction.channel_id):
            owner_id = int(db_value)
            break

    if owner_id is None:
        await interaction.response.send_message(config.NewTickets.Messages.thread_not_registered, ephemeral=True)
        return None

    if interaction.user.id != owner_id:
        await interaction.response.send_message(config.NewTickets.Messages.not_owner, ephemeral=True)
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
