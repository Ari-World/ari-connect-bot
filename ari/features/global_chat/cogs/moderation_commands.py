import functools
import logging

import discord
from discord import Embed
from discord.ext import commands

from ..services.moderation_service import ModerationService
from ..services.lobby_service import LobbyService
from ..services.relay_service import RelayService
from ..services.audit_log_service import AuditLogService

# This command is limited to level 1-2-3 role users

log = logging.getLogger("globalchat.moderation")


# Decorator for lobby required level
def level_required(required_level):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            if not self.moderation_service.is_authorized(ctx.author.id, required_level):
                await ctx.send(embed=discord.Embed(description=f"You don't have the required permission level {required_level} to use this command"))
                return
            return await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator


class Moderation(commands.Cog):
    def __init__(
            self,
            bot: commands.Bot,
            init,
            repositories,
            cache_manager,
            moderation_service: ModerationService,
            lobby_service: LobbyService,
            relay_service: RelayService,
            audit_log: AuditLogService):
        self.bot = bot
        self.init = init
        self.repos = repositories
        self.cache_manager = cache_manager
        self.moderation_service = moderation_service
        self.lobby_service = lobby_service
        self.relay_service = relay_service
        self.audit_log = audit_log

    # ===============================================================================================================
    # LEVEL 3 COMMANDS                                                                                              =
    # ===============================================================================================================

    @commands.hybrid_command(name="moderation", description="This command level 3 moderation access only")
    @level_required(3)
    async def GcCommands(self,ctx):

        embed = Embed(
            title="Moderation Commands",
            description= (
                "All Moderation commands is now available as a Slash command (experimental)\n but still try to work on normal commands"
            ),
            color=0xFFC0CB
        )
        embed.add_field(name="Global Chat Commands", value=(

            "`a!listmuted` - Shows all muted user globally\n"
            "`a!listbadwords` - Shows all banned words\n"
            "`a!listbadurls` - Shows all banned urls\n\n"

            "`a!mute <id> \" reason \"` - Mute user globally\n"
            "`a!unmute <id>` - Unmute user id\n\n"

            "`a!add_badlink \"word\"` - Add word to filter\n"
            "`a!remove_links \"word\"` - Remove word to the list\n\n"

            "`a!add_badwords \"word\"` - Add word to filter\n"
            "`a!remove_badwords \"word\"` - Remove word to the list\n\n"

            "`a!delete` - Reply to a message and just run this command, it will automatically delete message\n\n"

            "`a!reloaddata` - reload data in the cache\n"
            "Reason: beware, reloading unless necessary causes database query overload\n\n"

        ), inline=False)
        await ctx.send(embed = embed)

    @commands.hybrid_command(name='delete', description="This command level 3 moderation access only")
    @level_required(3)
    async def delete_message_by_mods(self, ctx):
        connection = self.lobby_service.find_connection(ctx.message.guild.id, ctx.message.channel.id)
        if not connection:
            await ctx.send(embed=Embed(description="This channel is not connected to any lobby"))
            return

        message_id = ctx.message.reference.message_id
        lobby_id = connection.lobby_id

        announce = await ctx.send(embed=Embed(description="Finding the message and deleting it..."))
        deleted = await self.relay_service.delete_relayed_message(lobby_id, message_id)

        if deleted:
            await announce.edit(embed=Embed(description=f"Message with the ID {message_id} has been deleted"))
            await self.audit_log.log_mod("Delete", {"message_id": message_id, "lobby_id": lobby_id}, ctx.message.author.id)
        else:
            await announce.edit(embed=Embed(
                description=f"**Unknown ID {message_id}**\n\n"
                            f"If this message has been out there for more than {self.cache_manager.deleteMessageThreshold / 60} mins, I will be unable to delete the message."))

    # Chat Moderation Commands
    @commands.hybrid_command(name='mute', description="This command level 3 moderation access only")
    @level_required(3)
    async def MuteUser(self, ctx, reason: str, id: int = None):
        connection = self.lobby_service.find_connection(ctx.message.guild.id, ctx.message.channel.id)
        if not connection:
            await ctx.send(embed=Embed(description="This channel is not connected to any lobby"))
            return

        target_message_id = id or ctx.message.reference.message_id
        messages_data = self.cache_manager.find_source_by_message_id(target_message_id, connection.lobby_id)
        source_entry = next((entry for entry in messages_data if entry.get('source')), None) if messages_data else None

        if not source_entry:
            await ctx.send(embed=Embed(description=" No User Found"))
            return

        user = await self.bot.fetch_user(source_entry["author"])
        if not user or user.bot:
            await ctx.send(embed=Embed(description=" No User Found"))
            return

        data = await self.moderation_service.mute_user(user.id, user.name, reason, ctx.message.author.name)
        await ctx.send(embed=Embed(description=f" User {user.id} ({user.name}) has been muted"))
        await self.audit_log.log_mod("Mute", data, ctx.message.author.id)

    @commands.hybrid_command(name='unmute', description="This command level 3 moderation access only")
    @level_required(3)
    async def UnMute(self, ctx, id: int = None):
        existing = await self.moderation_service.unmute_user(id)
        if not existing:
            await ctx.send(embed=Embed(description=" No User Found"))
            return

        sender = self.bot.get_user(id)
        if sender:
            await sender.send(embed=Embed(description="You have been unmuted from Global Chat!\n\n Welcome back! try to not get reported again"))
        await ctx.send(embed=Embed(description=f" User {existing.id} ({existing.name}) has been unmuted"))
        await self.audit_log.log_mod("Unmute", existing, ctx.message.author.id)

    # ===============================================================================================================
    # LEVEL 2 COMMANDS
    # ===============================================================================================================

    @commands.hybrid_command(name="listmuted", description="This command level 2 moderation access only")
    @level_required(3)
    async def getAllMuted(self,ctx):

        format_data = ""
        if self.init.muted_users:
            x=1
            for data in self.init.muted_users:
                text = f"{str(x)}) **{data.name} || {data.id}**\nReason : {data.reason}"
                format_data += text + "\n"
                x += 1
        else:
            format_data = "No users found."

        embed = Embed(
            title="Muted List",
            description=format_data
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="listbadwords", description="This command level 2 moderation access only")
    @level_required(3)
    async def getAllBadwords(self,ctx):

        format_data = ""
        if self.init.malicious_words:
            x=1
            for data in self.init.malicious_words:
                text = f"{str(x)}) {data.content} "
                format_data += text + "\n"
                x += 1

        embed = Embed(
            title="Banned Words",
            description=format_data
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="listbadurls", description="This command level 2 moderation access only")
    @level_required(3)
    async def getAllBadUrls(self,ctx):

        format_data = ""
        if self.init.malicious_urls:
            x=1
            for data in self.init.malicious_urls:
                text = f"{str(x)}) {data.content} "
                format_data += text + "\n"
                x += 1

        embed = Embed(
            title="Banned Urls",
            description=format_data
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='add_badlink', description="This command level 2 moderation access only")
    @level_required(2)
    async def AddblockLinks(self, ctx, content):
        await self.moderation_service.add_banned_url(content)
        await ctx.send(embed = Embed(
            description= f"Content has been added to list"
        ))
        await self.audit_log.log_mod("add_badlink",content,ctx.message.author.id)

    @commands.hybrid_command(name='remove_links', description="This command level 2 moderation access only")
    @level_required(2)
    async def RemoveBlockLinks(self, ctx, content):
        removed = await self.moderation_service.remove_banned_url(content)
        if removed:
            await ctx.send(embed=Embed(description=f" {removed.content} has been removed from the list"))
            await self.audit_log.log_mod("remove_links",removed,ctx.message.author.id)
        else:
            await ctx.send(embed=Embed(description=f"{content} not found in the list"))

    @commands.hybrid_command(name='add_badwords', description="This command level 2 moderation access only")
    @level_required(2)
    async def Addblockwords(self,ctx, content):
        await self.moderation_service.add_banned_word(content)
        await ctx.send(embed = Embed(
            description= f"Content has been added to list"
        ))
        await self.audit_log.log_mod("add_badwords",content,ctx.message.author.id)

    @commands.hybrid_command(name='remove_badwords', description="This command level 2 moderation access only")
    @level_required(2)
    async def RemoveBlockWorlds(self, ctx, content):
        removed = await self.moderation_service.remove_banned_word(content)
        if removed:
            await ctx.send(embed=Embed(description=f" {removed.content} has been removed from the list"))
            await self.audit_log.log_mod("remove_badwords",removed,ctx.message.author.id)
        else:
            await ctx.send(embed=Embed(description=f"{content} not found in the list"))

    # ===============================================================================================================
    # LEVEL 1 COMMANDS
    # ===============================================================================================================

    @commands.hybrid_command(name="listroles" , description="This command level 1 moderation access only")
    @level_required(1)
    async def getAllRoles(self,ctx):

        format_data = ""
        if self.init.moderator:
            x = 1
            for data in self.init.moderator:

                text = f" {data.icon} **{data.role_name}**\n Level: {data.level}\n"

                y = 1
                for mod in data.mods:
                    modText = f"> {str(y)}. {mod.name} ({mod.user_id})\n > Lobby: {mod.lobby_name}"

                    text += modText + "\n"
                    y +=1
                format_data += text + "\n"
        else:
            format_data = "No moderation roles found."
        embed = Embed(
            title="Moderation List Roles",
            description=format_data
        )
        await ctx.send(embed=embed)

    # ===============================================================================================================
    # OWNER COMMANDS
    # ===============================================================================================================
    @commands.hybrid_command(name="assign_role" , description="This command level 1 moderation access only")
    @level_required(1)
    async def assignRole(self, ctx, level, user_id, lobby):
        role_data = self.moderation_service.find_role_level(level)
        if role_data and any(mod.user_id == user_id for mod in role_data.mods):
            await ctx.send(embed=Embed(description=f"User ({user_id}) has already been assigned"))
            return
        if not role_data:
            await ctx.send(embed=Embed(description="Moderation level doesnt exists"))
            return

        lobby_name = lobby.upper() if lobby.lower() == "all" else lobby

        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound:
            await ctx.send(embed=Embed(description="User not found."))
            return
        except discord.HTTPException:
            await ctx.send(embed=Embed(description="An error occurred while fetching the user."))
            return

        success = await self.moderation_service.assign_role(level, user_id, user.name, lobby_name)

        if success:
            await ctx.send(embed=discord.Embed(description="Role assigned successfully."))
            await self.audit_log.log_mod("assign_role", {"user_id": user_id, "name": user.name, "lobby_name": lobby_name}, ctx.message.author.id)
        else:
            await ctx.send(embed=discord.Embed(description="Role assignment failed."))

    @commands.hybrid_command(name="create_role" , description="This command level 1 moderation access only")
    @level_required(1)
    async def createRole(self, ctx, level, role_name, icon):
        if self.moderation_service.find_role_level(level):
            await ctx.send(embed=Embed(description="Moderation level exists"))
            return

        success = await self.moderation_service.create_role(level, role_name, icon)

        if success:
            await ctx.send(embed=discord.Embed(description="Role creation successfully."))
            await self.audit_log.log_mod("create_role", {"role_name": role_name, "icon": str(icon), "level": level}, ctx.message.author.id)
        else:
            await ctx.send(embed=discord.Embed(description="Role creation failed."))

    @commands.hybrid_command(name="remove_role" , description="This command level 1 moderation access only")
    @level_required(1)
    async def removeRole(self, ctx, user_id ):
        role_data = self.moderation_service.find_role_by_user(user_id)
        if not role_data:
            await ctx.send(embed=Embed(description=f" User {user_id} doesnt exists"))
            return

        success = await self.moderation_service.remove_role(user_id)

        if success:
            await ctx.send(embed=discord.Embed(description="Role deletion successfully."))
            await self.audit_log.log_mod("remove_role", role_data, ctx.message.author.id)
        else:
            await ctx.send(embed=discord.Embed(description="Role deletion failed."))

    @commands.hybrid_command(name="reloaddata" , description="This command level 1 moderation access only")
    @level_required(1)
    async def reload(self, ctx):
        await self.init.load_data(
            self.repos.lobby_repository,
            self.repos.guild_repository,
            self.repos.lobby_config_repository,
            self.repos.muted_repository,
            self.repos.malicious_urls_repository,
            self.repos.malicious_words_repository,
            self.repos.moderator_repository)
        await ctx.send(embed=Embed(description="Data Loaded"))
