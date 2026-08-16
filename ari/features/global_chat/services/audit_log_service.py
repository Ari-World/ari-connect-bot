import logging

import discord
from discord import Embed
from discord.ext import commands

from .relay_service import MessageTypes
from ..persistence.state import GlobalChatState

log = logging.getLogger("globalchat.audit_log")


class AuditLogService:
    """Discord-side audit logging — the reporting/logging half of what used
    to live on `Intialization`. Reads its target channel ids off `state`
    (populated by `state.prepareLogging()`), and does nothing but send
    embeds to those channels.
    """

    def __init__(self, bot: commands.Bot, state: GlobalChatState):
        self.bot = bot
        self.state = state

    async def log_report(self, message, reason):
        guild = self.bot.get_guild(int(self.state.guild_logging_id))
        target_channel = guild.get_channel(int(self.state.system_logging_id))

        embed = Embed(
            title="Detected by system",
            description=f"**User {message.author.name} has been flagged due {reason}**\n\n**Message:**\n\n {message.content}"
        )
        embed.set_footer(text=f"userid {message.author.id}")
        await target_channel.send(embed=embed)

    async def chat_log_report(
            self, message: discord.Message,
            messageType,
            lobbyName,
            channel_id,
            message2: discord.Message = None):
        guild = self.bot.get_guild(int(self.state.guild_logging_id))
        target_channel = guild.get_channel(int(self.state.chat_logging_id))

        if messageType == MessageTypes.DELETE:
            embed = Embed(
                description="**Chat log**\n\n"
                f"**User**: {message.author.global_name}\n"
                "**Action**: Delete\n"
                f"**Lobby**: {lobbyName}\n"
                f"**Message**: {message.content}\n"
                )
            embed.set_footer(text=f"userid {message.author.id} || message ID {message.id}")
            await target_channel.send(embed=embed)
        elif messageType == MessageTypes.UPDATE:
            embed = Embed(
                description="**Chat log**\n\n"
                f"**User**: {message.author.global_name}\n"
                "**Action**: Edit\n"
                f"**Lobby**: {lobbyName}\n"
                f"**Before**: {message2.content}\n"
                f"**After**: {message.content}"
                )
            embed.set_footer(text=f"userid {message.author.id} || message ID {message2.id}")
            await target_channel.send(embed=embed)

    async def log_mod(self, action, data, user_id):
        guild = self.bot.get_guild(int(self.state.guild_logging_id))
        target_channel = guild.get_channel(int(self.state.mod_logging_id))

        user = await self.bot.fetch_user(user_id)
        embed = discord.Embed(
            title=f"{action} Command",
            description=(f"```{data}```")
        )
        embed.set_footer(text=f"{user.global_name}", icon_url=user.avatar.url)
        await target_channel.send(embed=embed)

    async def log_report_by_user(self, name, reportedBy, reason, attachments):
        guild = self.bot.get_guild(int(self.state.guild_logging_id))
        target_channel = guild.get_channel(int(self.state.player_report_logging_id))

        embed = discord.Embed(
            title="Reported",
            description=(f"**User {name} has reported**\n"
                          f"Reason: {reason}")
        )
        embed.set_footer(text=f"reported by {reportedBy}")

        if not isinstance(attachments, list):
            attachments = [attachments]

        for index, attachment in enumerate(attachments, start=1):
            embed.add_field(name=f"Proof {index}", value=attachment.url)

        await target_channel.send(embed=embed)
