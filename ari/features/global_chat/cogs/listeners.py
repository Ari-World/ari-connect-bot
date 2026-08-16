"""Discord event dispatch for global_chat — thin on purpose. Each handler's
only job is to figure out which connection a message belongs to and hand
off to `RelayService`; the actual relay engine lives there.
"""
import logging

import discord
from discord.ext import commands

from ..services.relay_service import RelayService, MessageTypes
from ..services.lobby_service import LobbyService

log = logging.getLogger("globalchat.listener")


class EventListeners(commands.Cog):
    def __init__(self, bot: commands.Bot, init, relay_service: RelayService, lobby_service: LobbyService):
        self.bot = bot
        self.init = init
        self.relay_service = relay_service
        self.lobby_service = lobby_service

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.id in self.init.bypass_delete_listener:
            return

        if message.author.bot:
            return

        connection = self.lobby_service.find_connection(message.guild.id, message.channel.id)
        if not connection:
            return

        await self.relay_service.relay(message, connection, MessageTypes.DELETE)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.content.startswith(self.bot.command_prefix) or before.author.bot:
            return

        connection = self.lobby_service.find_connection(before.guild.id, before.channel.id)
        if not connection:
            return

        # TODO: Moderation for global chat — see moderation_service (issue 008)

        await self.relay_service.relay(after, connection, MessageTypes.UPDATE)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content.startswith(self.bot.command_prefix) or message.author.bot:
            return

        connection = self.lobby_service.find_connection(message.guild.id, message.channel.id)
        if not connection:
            return

        # TODO: Moderation (muted users / malicious content) — see moderation_service (issue 008)

        message_type = MessageTypes.REPLY if message.type == discord.MessageType.reply else MessageTypes.SEND
        await self.relay_service.relay(message, connection, message_type)
