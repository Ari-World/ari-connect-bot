"""Connect/unlink/switch orchestration: create/delete the real Discord
webhook, persist the connection record, and update `GlobalChatState`'s
cache — the three things `Chat`'s command bodies and `CreateLobbyModal`
used to do inline. Also owns the join/switch announcement broadcast
(`announce_join`), since that's part of a connection's lifecycle, not
message relay (see issue 005's log for why it didn't move to
`relay_service.py` as the PRD originally sketched).
"""
import asyncio
import logging

import discord
from discord import Embed, Webhook
import aiohttp
from discord.ext import commands

from ..domain.models import Connection
from ..persistence.state import GlobalChatState

log = logging.getLogger("globalchat.guild_connection_service")


class GuildConnectionService:
    def __init__(self, bot: commands.Bot, state: GlobalChatState, repository):
        self.bot = bot
        self.state = state
        self.repos = repository

    async def connect(self, channel: discord.TextChannel, guild: discord.Guild, lobby_id: str, lobby_title: str) -> Connection:
        webhook = await channel.create_webhook(name=lobby_title)
        connection = Connection(
            lobby_id=lobby_id,
            channel_id=channel.id,
            webhook=webhook.url,
            guild_id=guild.id,
            guild_name=guild.name,
        )
        connection = await self.repos.guild_repository.create(connection)
        self.state.connection.append(connection)
        return connection

    async def disconnect(self, connection: Connection) -> None:
        channel = self.bot.get_channel(connection.channel_id)
        if channel:
            webhooks = await channel.webhooks()
            for webhook in webhooks:
                if webhook.url == connection.webhook:
                    await webhook.delete()
                    break

        await self.repos.guild_repository.delete(connection)
        self.state.connection.remove(connection)

    async def switch(self, channel: discord.TextChannel, guild: discord.Guild, current_connection: Connection, new_lobby_id: str, new_lobby_title: str) -> Connection:
        await self.disconnect(current_connection)
        return await self.connect(channel, guild, new_lobby_id, new_lobby_title)

    async def announce_join(self, announcing_guild: discord.Guild, source_channel_id: int, lobby_id: str) -> None:
        async with aiohttp.ClientSession() as session:
            tasks = []

            for connection in self.state.connection:
                if connection.channel_id != source_channel_id and str(connection.lobby_id) == str(lobby_id):
                    webhook = Webhook.from_url(connection.webhook, session=session)
                    embed = Embed(color=0xEB459F)
                    embed.set_author(name=f"{announcing_guild.name} has joined the chat", icon_url=announcing_guild.icon.url)

                    tasks.append(
                        webhook.send(
                            avatar_url=self.bot.user.avatar.url,
                            username=self.bot.user.name,
                            embed=embed,
                            wait=True,
                        )
                    )

            await asyncio.gather(*tasks)
