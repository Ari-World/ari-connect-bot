import asyncio
import logging
import discord
from discord.ext import commands
from discord import Embed

from ..ui.views import CreateLobbyModal, LobbyPagination
from ..persistence.state import GlobalChatState
from ..services.audit_log_service import AuditLogService
from ..services.lobby_service import LobbyService
from ..services.guild_connection_service import GuildConnectionService
from ..ui import presenters

log = logging.getLogger("globalchat.commands")

class Chat(commands.Cog):
    def __init__(
            self,
            bot: commands.Bot,
            initialization: GlobalChatState,
            repositories,
            audit_log: AuditLogService,
            lobby_service: LobbyService,
            guild_connection_service: GuildConnectionService):
        self.bot = bot
        self.init = initialization
        self.repos = repositories
        self.audit_log = audit_log
        self.lobby_service = lobby_service
        self.guild_connection_service = guild_connection_service

    # Conditions: Perms to kick user
    @commands.hybrid_command(name='createlobby',with_app_command=True, description='Create a global chat lobby, 1 per server')
    @commands.has_permissions(kick_members=True)
    async def createLobby(self, ctx:commands.Context):

        guild_id = ctx.guild.id
        canCreate = False

        for lobby in self.init.lobby_data:
            if guild_id == lobby.guild_id:
                log.info(lobby)
                canCreate = True
                break

        if not canCreate:
            modal = CreateLobbyModal(self.lobby_service, self.guild_connection_service)
            response = await ctx.interaction.response.send_modal(modal)
        else:
            await ctx.send(embed=presenters.build_simple_embed(":no_entry: You have reached the limit of 1 lobby per server", color=0xFFC0CB))


    @commands.hybrid_command(name='lobby_show', description="Shows more information of the lobby using the code")
    async def showlobbyData(self, ctx: commands.Context, lobby_id: str):
        lobby_details = self.lobby_service.find_lobby_details(lobby_id)
        if not lobby_details:
            await ctx.send(embed=presenters.build_simple_embed("Lobby not found", color=0xFFC0CB))
            return

        guild_data = await self.bot.fetch_guild(lobby_details.guild_id)
        connections = self.lobby_service.connections_for_lobby(lobby_id)

        embed = presenters.build_lobby_detail_embed(
            lobby_details,
            str(guild_data.icon.url) if guild_data.icon else None,
            guild_data.name,
            guild_data.approximate_member_count,
            len(connections),
            [conn.guild_name for conn in connections],
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='lobbies', description='Current Lobby description')
    async def show_lobbies(self, ctx: commands.Context):

        view = LobbyPagination(self.lobby_service)
        view.load_data()
        await view.send(ctx)

    @commands.hybrid_command(name='connect', description='Link to Open World')
    @commands.has_permissions(kick_members=True)
    async def openworldlink(self, ctx : commands.Context, lobby_id: str = None):

        guild = ctx.guild
        channel = ctx.channel

        if self.lobby_service.find_connection(guild.id, channel.id):
            embed = presenters.build_simple_embed(
                "Type `a!unlink` to unlink your Open World\n*This will only unlink from the Open World channel*",
                title=":no_entry: Your channel is already registered for Open World Chat",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)
            return

        if lobby_id:
            lobby_details = self.lobby_service.find_lobby_details(lobby_id)
            if not lobby_details:
                await ctx.send(embed=presenters.build_simple_embed(
                    None, title=":no_entry: The lobby ID that you have provided is not available", color=0xFF0000))
                return

            if not self.lobby_service.has_room(lobby_details):
                await ctx.send(embed=presenters.build_simple_embed(None, title=":no_entry: Lobby is full", color=0xFF0000))
                return
            # else if the lobby id is not provided then we'll do the auto connect feature
        else:
            # TODO: Implement a auto connect feautre
            lobby_id = self.init.generalLobby
            lobby_details = self.lobby_service.find_lobby_details(lobby_id)
            if not lobby_details:
                await ctx.send(embed=presenters.build_simple_embed(
                    None, title=":⚠️: Auto Connect Feature is under-development", color=0xFF0000))
                return
            # This should always be true

        # Connect it
        await self.guild_connection_service.connect(channel, guild, lobby_id, lobby_details.title)

        # Send a success message if its successfull
        await ctx.send(embed=presenters.build_connect_success_embed(lobby_details.title))
        await asyncio.sleep(1)
        message = await ctx.send(embed=presenters.build_connect_thanks_embed(self.init.openworldThanksMessage))
        await message.add_reaction('✅')

        await self.guild_connection_service.announce_join(guild, channel.id, lobby_id)

    @commands.hybrid_command(name='unlink', description='Unlink from Open World')
    @commands.has_permissions(kick_members=True)
    async def openworldunlink(self, ctx: commands.Context):
        connection = self.lobby_service.find_connection(ctx.guild.id, ctx.channel.id)

        if connection:
            await self.guild_connection_service.disconnect(connection)
            await ctx.send(embed=presenters.build_simple_embed(":white_check_mark: **Unlinked from Open World Chat**", color=0x00FF00))
        else:
            await ctx.send(embed=presenters.build_simple_embed(":no_entry: **Your channel is not registered for Open World Chat**", color=0xFF0000))

    #Get Current Lobby
    @commands.hybrid_command(name='current', description='Current Lobby description')
    async def current_lobby(self, ctx: commands.Context):
        connection = self.lobby_service.find_connection(ctx.guild.id, ctx.channel.id)
        if not connection:
            await ctx.send(embed=presenters.build_simple_embed(
                None, title=":no_entry: This channel is not connected to any channel", color=0xFF0000))
            return

        lobby_details = self.lobby_service.find_lobby_details(connection.lobby_id)
        if not lobby_details:
            await ctx.send(embed=presenters.build_simple_embed(
                "⚠️ **Something went wrong when searching for the lobby**", color=0xFFC0CB))
            return

        guild_data = await self.bot.fetch_guild(lobby_details.guild_id)
        connections = self.lobby_service.connections_for_lobby(lobby_details.lobby_id)

        embed = presenters.build_lobby_detail_embed(
            lobby_details,
            str(guild_data.icon.url) if guild_data.icon else None,
            guild_data.name,
            guild_data.approximate_member_count,
            len(connections),
            [conn.guild_name for conn in connections],
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='switch', description='Switch to a different server lobby')
    @commands.has_permissions(kick_members=True)
    async def switch_lobby(self, ctx: commands.Context, lobby_id : str):
        guild = ctx.guild
        channel = ctx.channel

        connection = self.lobby_service.find_connection(guild.id, channel.id)
        lobby_details = self.lobby_service.find_lobby_details(lobby_id)

        if not connection or not lobby_details:
            await ctx.send(embed=presenters.build_simple_embed(
                ":no_entry: **Your channel is not registered for Open World Chat**", color=0x7289DA))
            return

        await self.guild_connection_service.switch(channel, guild, connection, lobby_id, lobby_details.title)

        await ctx.send(embed=presenters.build_switch_success_embed(lobby_details.title))
        await self.guild_connection_service.announce_join(guild, channel.id, lobby_id)

    @commands.hybrid_command(name="report",description="Report a user for misbehaving, and attach a picture for proff")
    async def report_user(self, ctx, username, reason, attacment:discord.Attachment = None):

        await ctx.send(embed=discord.Embed(description=f"User has been reported"))
        await self.audit_log.log_report_by_user(username,ctx.author.name,reason,attacment)
