"""Pure embed-building functions for global_chat's Discord UI.

No `ctx.send`/network calls in here — cogs call these to get a
`discord.Embed`, then send/edit it themselves.
"""
from typing import List, Optional

import discord

from core.utils.utility import Color
from ..domain.models import LobbyView, LobbyDetails, ModerationConfig, LogConfig

_BLANK = "<:_blank:1266299283737677844>"


def build_simple_embed(description: str, *, title: str = None, color: int = 0x7289DA) -> discord.Embed:
    """A one-off status embed — most of the connect/unlink/switch flow's
    success/error messages are just this."""
    return discord.Embed(title=title, description=description, color=color)


def build_connect_success_embed(lobby_title: str) -> discord.Embed:
    return discord.Embed(
        description=f':white_check_mark: **LINK START!! You are now connected to {lobby_title}**',
        color=0x7289DA
    )


def build_connect_thanks_embed(thanks_message: str) -> discord.Embed:
    return discord.Embed(
        title="Thank you for linking with Open World Server!",
        description=thanks_message,
        color=0x00FF00
    )


def build_lobby_created_embed(title: str, lobby_id: str, description: str, topics: List[str], limit: int = 20) -> discord.Embed:
    topics_text = " ".join(f"`{topic}`" for topic in topics)
    embed = discord.Embed(
        title=title,
        description=f"> **Connections:** `1/{limit}` \n> **Lobby code:** {lobby_id}",
        color=0xFFC0CB
    )
    embed.add_field(name="Topics", value=topics_text, inline=False)
    embed.add_field(name="Description", value=description, inline=False)
    return embed


def build_switch_success_embed(lobby_title: str) -> discord.Embed:
    return discord.Embed(
        description=f":white_check_mark: **You have switched to {lobby_title}**",
        color=0x7289DA
    )


def build_lobby_pagination_embed(data: List[LobbyView], current_page: int, total_pages: int, icon_url: Optional[str] = None) -> discord.Embed:
    embed = discord.Embed(title="Open Lobbies", color=0xFFC0CB)
    embed.set_footer(text=f"page {current_page} / {total_pages}", icon_url=icon_url)
    embed.add_field(
        name="Checkout the following commands!",
        inline=False,
        value=
            "`/global_show <lobbycode>` To view more about the lobby\n"
            "`/connect <lobbycode>` Join the lobby and have a chat\n\n"
            "Visit the website search more lobby: [Website](https://ariconnect.vercel.app/)"
    )

    for item in data:
        limit = 1
        topics = ""
        for topic in item.topics:
            if limit > 5:
                break
            topics += f"`{topic}` "
            limit += 1

        embed.add_field(
            name=f"{item.title} {item.connection_count}/{item.limit}",
            inline=False,
            value=f"{topics}\nLobby code: {item.lobby_id}"
        )
    return embed


def build_lobby_detail_embed(
        lobby_details: LobbyView,
        guild_icon_url: Optional[str],
        guild_name: str,
        member_count: Optional[int],
        connection_count: int,
        connected_guild_names: List[str]) -> discord.Embed:
    """The "show me this lobby" view — used by both `/current` and
    `/lobby_show`, which used to duplicate this exact embed."""
    topics = " ".join(f"`{topic}`" for topic in lobby_details.topics)

    embed = discord.Embed(title=lobby_details.title, color=0xFFC0CB)
    if guild_icon_url:
        embed.set_thumbnail(url=guild_icon_url)
    embed.add_field(name="Host", value=f"**Name:** {guild_name} \n**Members:** {member_count}", inline=True)
    embed.add_field(
        name="Info",
        value=f"Connections: `{connection_count}/{lobby_details.limit}` \n"
              f" Lobby code: {lobby_details.lobby_id}",
        inline=True)
    embed.add_field(name="Description", value=lobby_details.description, inline=False)
    embed.add_field(name="Topics", value=topics, inline=False)
    embed.add_field(name="Connections", value="\n".join(connected_guild_names) or "There's no guild connected yet", inline=False)
    embed.set_footer(text="Custom Message here")
    return embed

SETTINGS_MENU_FIELDS = [
    {
        "title": "Lobby Details",
        "description": f"{_BLANK}Edit",
        "value": "lobbydetails",
        "emoji": "🔎",
        "inline": True
    },
    {
        "title": "Moderation",
        "description": f"{_BLANK}Change",
        "value": "moderation",
        "emoji": "🛠️",
        "inline": True
    },
    {
        "title": "Logging",
        "description": f"{_BLANK}Change",
        "value": "logging",
        "emoji": "📝",
        "inline": True
    }
]


def build_menu_embed(title: str, icon_url: str, description: str = None, fields: list = None) -> discord.Embed:
    embed = discord.Embed(color=Color.PRIMARY.to_discord_color(), description=description)
    embed.set_author(name=f"Ari connect - {title}", icon_url=icon_url)

    if fields:
        for field in fields:
            embed.add_field(name=f"{field['emoji']} {field['title']}", value=field['description'], inline=field['inline'])

    return embed


def lobby_details_fields(lobby_details: LobbyDetails) -> list:
    return [
        {
            "title": "Title",
            "description": f"{_BLANK}{lobby_details.title}",
            "value": "title",
            "emoji": "💬",
            "inline": False
        },
        {
            "title": "Description",
            "description": f"{_BLANK} {lobby_details.description}",
            "value": "description",
            "emoji": "📝",
            "inline": False
        },
        {
            "title": "Topics",
            "description": f"{_BLANK} {lobby_details.topics}",
            "value": "topics",
            "emoji": "🔎",
            "inline": False
        }
    ]


def moderation_fields(moderation_config: ModerationConfig) -> list:
    return [
        {
            "title": "Moderators",
            "description": f"{_BLANK} {len(moderation_config.moderators)}",
            "value": "moderators",
            "emoji": "🛡️",
            "inline": False
        },
        {
            "title": "Banned Words",
            "description": f"{_BLANK} {len(moderation_config.banned_words)}",
            "value": "bannedwords",
            "emoji": "💬",
            "inline": False
        },
        {
            "title": "Banned Links",
            "description": f"{_BLANK} {len(moderation_config.banned_links)}",
            "value": "bannedlinks",
            "emoji": "🔗",
            "inline": False
        },
        {
            "title": "Banned users",
            "description": f"{_BLANK} {len(moderation_config.banned_users)}",
            "value": "bannedusers",
            "emoji": "👤",
            "inline": False
        },
        {
            "title": "Banned servers",
            "description": f"{_BLANK} {len(moderation_config.banned_server)}",
            "value": "bannedservers",
            "emoji": "🌐",
            "inline": False
        }
    ]


def logging_fields(logging_config: LogConfig) -> list:
    return [
        {
            "title": "Chat Logs",
            "description": f"{_BLANK} {logging_config.chat_log.channel_id}",
            "value": "chatlogs",
            "emoji": "💬",
            "inline": True
        },
        {
            "title": "Moderation Logs",
            "description": f"{_BLANK} {logging_config.moderation_log.channel_id}",
            "value": "moderationlogs",
            "emoji": "📝",
            "inline": True
        },
        {
            "title": "Report Logs",
            "description": f"{_BLANK} {logging_config.report_logs.channel_id}",
            "value": "reportlogs",
            "emoji": "🔎",
            "inline": True
        }
    ]
