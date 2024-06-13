
import asyncio
import logging
import aiohttp
from discord import Embed, Webhook
import discord
from discord.ext import commands

import functools

# This command is limited to level 1-2-3 role users

log = logging.getLogger("globalchat.moderation")


# Decorator for lobby required level
def level_required(required_level):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            user_level = self.init.get_user_level(ctx.author.id)
            if user_level >= required_level+ 1:
                await ctx.send(embed=discord.Embed(description=f"You don't have the required permission level {required_level} to use this command"))
                return
            return await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator


class Moderation(commands.Cog):
    def __init__(self, bot:commands.Bot, repositories, initialization, cacheManager):
        self.bot = bot
        self.repos = repositories
        self.init = initialization
        self.cache_manager = cacheManager
    
    # ===============================================================================================================
    # LEVEL 3 COMMANDS                                                                                              =
    # =============================================================================================================== 
    
    # TODO: Improve Embed
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

            "`a!add_lobby \"Lobby Name\"` - Add public global chat\n"
            "`a!remove_lobby \"Lobby Name\"` - Remove public chat\n\n"
            
            "`a!add_badlink \"word\"` - Add word to filter\n"
            "`a!remove_links \"word\"` - Remove word to the list\n\n"

            "`a!add_badwords \"word\"` - Add word to filter\n"
            "`a!remove_badwords \"word\"` - Remove word to the list\n\n"
            
            "`a!delete` - Reply to a message and just run this command, it will automatically delete message\n\n" 

            "**Deprecated Commands**\n"
            "`a!reload data`- reload data in the cache (still working)\n"
            "Reason: Removed because its already automated, beware to reload data unless necessary causes database query overload\n\n"
        
        ), inline=False)
        await ctx.send(embed = embed)

    @commands.hybrid_command(name='delete', description="This command level 3 moderation access only")
    @level_required(3)
    async def delete_message_by_mods(self, ctx):
        
        guild_id = ctx.message.guild.id
        channel_id = ctx.message.channel.id
        guild_document = self.init.find_guild(guild_id, channel_id)
        
        for channel in guild_document["channels"]:
            if channel["channel_id"] == channel_id:
                matched_data = channel
                break
        message_id = ctx.message.reference.message_id
        data = {
            "message_id":message_id, 
            "lobby_name":matched_data["lobby_name"],
        }

        await self.handle_delete_by_command(message_id, matched_data["lobby_name"], ctx)  
        await self.init.log_mod("Delete", data, ctx.message.author.id)

    async def handle_delete_by_command(self, message_id, lobby_name, ctx):
        announce = await ctx.send(embed = Embed(description="Finding the Message in the cache"))
        
        source_data = self.cache_manager.find_source_data(int(message_id), lobby_name)

        if source_data:
            combined_ids = [{"channel": source_data["channel"], "messageId": source_data["source"]}]
            combined_ids.extend(data for data in source_data["webhooksent"])
        else:
            await announce.edit(embed=Embed(description=f"**Unknown ID {message_id}**\n\n"
                                       f"If this message has been out there for more than {self.cache_manager.deleteMessageThreshold / 60} mins, I will be unable to delete the message."))
            return
        await announce.edit(embed= Embed(description="Commencing the deletion of the message"))
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            async def update_loading_message():
                loading_stages = ["Deleting message.", "Deleting message..", "Deleting message..."]
                stage_index = 0
                while not all_tasks_done.is_set():
                    await announce.edit(embed=Embed(description=loading_stages[stage_index]))
                    stage_index = (stage_index + 1) % len(loading_stages)
                    await asyncio.sleep(1)
            
            all_tasks_done = asyncio.Event()
            update_task = asyncio.create_task(update_loading_message())
            try:
                for document in self.init.guild_data:
                    for channel in document["channels"]:
                        if channel["lobby_name"] == str(lobby_name):
                            webhook  = Webhook.from_url(channel["webhook"], session=session)
                            message = await self.init.find_messageID(channel["channel_id"],combined_ids)
                            tasks.append( self.process_delete_message_by_mods(webhook, message.id, channel["channel_id"]))

                await asyncio.gather(*tasks)
            finally:
                all_tasks_done.set()
                await update_task
            await announce.edit(embed = Embed(description=f"Message with the ID {message_id} has been deleted"))

    async def process_delete_message_by_mods(self ,webhook ,message_id,channel):
        try:
            await webhook.edit_message(
                message_id,
                content = "*[message deleted by moderator]*",
                attachments = [],
                embeds = []
            )
        except Exception as e:
            try:
                self.init.bypass_delete_listener.add(message_id)

                sourceChannel = self.bot.get_channel(int(channel))
                message = await sourceChannel.fetch_message(message_id)

                if message is None:
                    log.error(f"Message with ID {message_id} not found in channel {channel}")
                    return
            
                try:
                    await message.delete()
                    description = (
                    "Your message has been deleted by the moderator."
                    " Please be mindful of what you send.\n\n"
                    f"Content: {message.content}"
                    )

                    # Handle attachments
                    if message.attachments:
                        attachment_urls = "\n".join([attachment.url for attachment in message.attachments])
                        description += f"\n\nAttachments:\n{attachment_urls}"

                    embed = Embed(description=description)
                
                    # Set the first attachment as the embed image if it exists
                    if message.attachments:
                        embed.set_image(url=message.attachments[0].url)

                    await message.author.send(embed=embed)
                except Exception as edit_e:
                    log.error(f"Failed to edit the message: {edit_e}")
                    if hasattr(edit_e, 'code'):
                        log.error(f"Discord API Error Code: {edit_e.code}")
                finally:
                    self.init.bypass_delete_listener.remove(message_id)
     
            except Exception as inner_e:
                    log.warning(f"Failed to fetch or edit message: {inner_e}")
    
    

    # Chat Moderation Commands
    @commands.hybrid_command(name='mute', description="This command level 2 moderation access only")
    @level_required(3)
    async def MuteUser(self, ctx,reason:str, id : int = None):
        
        user = None
        if not id:
            # If id is not provided
            guild_id = ctx.message.guild.id
            channel_id = ctx.message.channel.id
            guild_document = self.init.find_guild(guild_id, channel_id)
            
            for channel in guild_document["channels"]:
                if channel["channel_id"] == channel_id:
                    lobby_name = channel["lobby_name"]
                    break

            source = self.cache_manager.find_source_data(ctx.message.reference.message_id, lobby_name)

            user = await self.bot.fetch_user(source["author"])

        else:
            guild_id = ctx.message.guild.id
            channel_id = ctx.message.channel.id
            guild_document = self.init.find_guild(guild_id, channel_id)

            for channel in guild_document["channels"]:
                if channel["channel_id"] == channel_id:
                    lobby_name = channel["lobby_name"]
            source = self.cache_manager.find_source_data(id, lobby_name)

            user = await self.bot.fetch_user(source["source"])
            
        if user.bot or not user:
                await ctx.send(embed=Embed( description=" No User Found"))
                return
    
        data = {
            "id": user.id,
            "name" : user.name,
            "reason": reason,
            "mutedBy" : ctx.message.author.name
        }

        await self.repos.muted_repository.create(data)
        self.init.muted_users.append(data)
        await ctx.send(embed=Embed( description=f" User {user.id} ({user.name}) has been muted"))
        await self.init.log_mod("Mute",data,ctx.message.author.id)

    @commands.hybrid_command(name='unmute', description="This command level 3 moderation access only")
    @level_required(3)
    async def UnMute(self, ctx, id: int = None):
        
      
        
        exists = None
        for data in self.init.muted_users:
            if data["id"] == id:
                exists = data
        
        if not exists:
                await ctx.send(embed=Embed( description=" No User Found"))
                return
        
          
        sender = self.bot.get_user(id) 
        await self.repos.muted_repository.delete(exists["id"])
        self.init.muted_users.remove(exists)
        await sender.send(embed=Embed(description=f"You have been unmuted from Global Chat!\n\n Welcome back! try to not get reported again"))
        await ctx.send(embed=Embed( description=f" User {exists["id"]} ({exists["name"]}) has been unmuted"))
        await self.init.log_mod("Unmute",exists,ctx.message.author.id)

    # ===============================================================================================================
    # LEVEL 2 COMMANDS 
    # ===============================================================================================================
    
    # TODO: Improve Embed
    @commands.hybrid_command(name="listmuted", description="This command level 2 moderation access only")
    @level_required(3)
    async def getAllMuted(self,ctx):
       
        format_data = ""
        if self.init.muted_users:
            x=1
            for data in self.init.muted_users:
                text = f"{str(x)}) **{data['name']} || {data['id']}**\nReason : {data['reason']}"
                format_data += text + "\n"
                x += 1
        else:
            format_data = "No users found."

        embed = Embed(
            title="Muted List",
            description=format_data
        )
        await ctx.send(embed=embed)

    # TODO: Improve Embed
    @commands.hybrid_command(name="listbadwords", description="This command level 2 moderation access only")
    @level_required(3)
    async def getAllBadwords(self,ctx):
        

        format_data = ""
        if self.init.malicious_words:
            x=1
            for data in self.init.malicious_words:
                text = f"{str(x)}) {data["content"]} "
                format_data += text + "\n"
                x += 1

        embed = Embed(
            title="Banned Words",
            description=format_data
        )
        await ctx.send(embed=embed)

    # TODO: Improve Embed
    @commands.hybrid_command(name="listbadurls", description="This command level 2 moderation access only")
    @level_required(3)
    async def getAllBadUrls(self,ctx):
        
        format_data = ""
        if self.init.malicious_urls:
            x=1
            for data in self.init.malicious_urls:
                text = f"{str(x)}) {data["content"]} "
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
       
        self.init.malicious_urls.append({"content":content})
        await self.repos.malicious_urls_repository.create(content)
        await ctx.send(embed = Embed(
            description= f"Content has been added to list"
        ))
        await self.init.log_mod("add_badlink",content,ctx.message.author.id)
    
    @commands.hybrid_command(name='remove_links', description="This command level 2 moderation access only")
    @level_required(2)
    async def RemoveBlockLinks(self, ctx, content):
       
        exists = await self.repos.malicious_urls_repository.findOne(content)
 
        if exists:
            await self.repos.muted_repository.delete(exists["content"])
            self.init.malicious_urls.remove(exists)
            await ctx.send(embed=Embed( description=f" {exists["content"]} has been removed to the list"))
            await self.init.log_mod("remove_links",exists,ctx.message.author.id)
        else:    
            await ctx.send(embed=Embed( description=f"{content}not found in the list"))

    @commands.hybrid_command(name='add_badwords', description="This command level 2 moderation access only")
    @level_required(2)
    async def Addblockwords(self,ctx, content):

        
        self.init.malicious_words.append({"content":content})
        await self.repos.malicious_words_repository.create(content)
        await ctx.send(embed = Embed(
            description= f"Content has been added to list"
        ))
        await self.init.log_mod("add_badwords",content,ctx.message.author.id)

    
    @commands.hybrid_command(name='remove_badwords', description="This command level 2 moderation access only")
    @level_required(2)
    async def RemoveBlockWorlds(self, ctx, content):
        
        exists = await self.repos.malicious_words_repository.findOne(content)
 
        if exists:
            await self.repos.muted_repository.delete(exists["content"])
            self.init.malicious_words.remove(exists)
            await ctx.send(embed=Embed( description=f" {exists["content"]} has been removed to the list"))
            await self.init.log_mod("remove_badwords",exists,ctx.message.author.id)
        else:    
            await ctx.send(embed=Embed( description=f"{content}not found in the list"))

    # ===============================================================================================================
    # LEVEL 1 COMMANDS 
    # ===============================================================================================================
    
    
    # TODO: Improve Embed
    @commands.hybrid_command(name="listroles" , description="This command level 1 moderation access only")
    @level_required(1)
    async def getAllRoles(self,ctx):
        
        format_data = ""
        if self.init.moderator:
            x = 1
            for data in self.init.moderator:
                
                text = f" {data["icon"]} **{data['role_name']}**\n Level: {data['level']}\n"
                
                y = 1
                for mod in data["mods"]:
                    modText = f"> {str(y)}. {mod['name']} ({mod['user_id']})\n > Lobby: {mod['lobby_name']}"

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
        
        # Checks if the role level is valid
        data = None
        for data in self.init.moderator:
            if data["level"] == level:
                for mod in data["mods"]:
                    if mod["user_id"] == user_id:
                        await ctx.send(embed = Embed(description=f"User ({user_id})has all ready been assigned"))
                        return
                break

        if data is None:
            await ctx.send(embed = Embed(description="Moderation level doesnt exists"))
            return
        
        lobby_name = lobby.upper() if lobby.lower() == "all" else lobby

        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound:        
            await ctx.send(embed = Embed(description="User not found."))
        except discord.HTTPException:
            await ctx.send(embed = Embed(description="An error occurred while fetching the user."))
        
        role = {
            "user_id" :user_id,
            "name" : user.name,
            "lobby_name" : lobby_name
        }

        result = await self.repos.create_moderator_role(role,level)
        
        if result:
            await ctx.send(embed=discord.Embed(description="Role assigned successfully."))
            await self.init.log_mod("assign_role",role,ctx.message.author.id)
        else:
            await ctx.send(embed=discord.Embed(description="Role assignment failed."))

    @commands.hybrid_command(name="create_role" , description="This command level 1 moderation access only")
    @level_required(1)
    async def createRole(self, ctx, level, role_name, icon):
        
        for data in self.init.moderator:
            if data["level"] == level:
                await ctx.send(embed = Embed(description="Moderation level exists"))
                return
        
        role = {
            "role_name" : role_name,
            "icon": str(icon),
            "level": level,
            "mods": []
        }
        log.info(role)
        result = await self.repos.create_moderator_role(role, level)

        if result:
            await ctx.send(embed=discord.Embed(description="Role creation successfully."))
            await self.init.log_mod("create_role",role,ctx.message.author.id)
        else:
            await ctx.send(embed=discord.Embed(description="Role creation failed."))
    
    @commands.hybrid_command(name="remove_role" , description="This command level 1 moderation access only")
    @level_required(1)
    async def removeRole(self, ctx, user_id ):

        modData = None
        role = None
        for data in self.init.moderator:
            for mod in data["mods"]:
                if mod["user_id"] == user_id:
                    modData = data
                    role = mod
                    break
                
        if modData is None:
            await ctx.send(embed = Embed(description=f" User {user_id} doesnt exists"))
            return
        result = await self.repos.delete_moderator_assigned_lobby(modData,role)

        if result:
            await ctx.send(embed=discord.Embed(description="Role deletion successfully."))
            await self.init.log_mod("remove_role",modData,ctx.message.author.id)
        else:
            await ctx.send(embed=discord.Embed(description="Role deletion failed."))
        
    @commands.hybrid_command(name='add_lobby' , description="This command level 1 moderation access only")
    @level_required(1)
    async def AddLobbies(self, ctx, name:str, description: str ,limit:int):
       
        
        if self.init.server_lobbies:
            for x in self.init.server_lobbies:
                if name == x['lobbyname']:
                    await ctx.send(embed=discord.Embed( description="Lobby Exists"))
                    return

        data = {
            "lobbyname":name,
            "description": description,
            "limit":limit
        }
        await self.repos.lobby_repository.create(data)
        self.init.server_lobbies.append(data)
        await ctx.send(embed=discord.Embed( description=f" Lobby {name} has been newly added"))
        await self.init.log_mod("add_lobby",data,ctx.message.author.id)


    @commands.hybrid_command(name="addhooks" , description="This command level 1 moderation access only")
    @level_required(1)
    async def addHooks(self,ctx :commands.Context):

        msg = await ctx.send(embed = Embed( description="Checking discord webhooks in channels"))
        changes = []
        errors = []
        
        for guild in self.init.guild_data:
            for channel in guild["channels"]:
                try:
                    chnlObj = await self.bot.fetch_channel(channel["channel_id"])
                    
                    if "webhook" not in channel:
                        webhook = await chnlObj.create_webhook(name=guild["server_name"])
                        channel["webhook"] = webhook.url  # Assign webhook URL
                        changes.append(f"{guild["server_name"]} webhook created")
                    elif "webhook" in channel:
                        # Check if the webhook still exists in the channel
                        existing_webhooks = await chnlObj.webhooks()
                        webhook_url = channel["webhook"]
                        if not any(webhook.url == webhook_url for webhook in existing_webhooks):
                            # Recreate the webhook if it doesn't exist
                            webhook = await chnlObj.create_webhook(name=guild["server_name"])
                            channel["webhook"] = webhook.url  # Assign webhook URL
                            changes.append(f"{guild["server_name"]} webhook updated")

                except Exception as e:
                    errors.append(f"{guild['server_name']} : {e}")
                    
            await self.repos.guild_repository.update({
                "server_id": guild["server_id"],
                "channels": guild["channels"]
            })

        await msg.edit(embed = Embed( description="Writing reports"))
        message = "Webhooks in all channels of each server has been refreshed"
        embed = Embed(
                title = "Report",
                description= message
            )
        if changes:
            text = ""
            for data in changes:
                text += data
            embed.add_field(name="Report",value=text)

        if errors:
            text = ""
            for data in errors:
                text += data
            embed.add_field(name="Errors",value=text)

        await msg.edit(embed=embed)

    @commands.hybrid_command(name="reloaddata" , description="This command level 1 moderation access only")
    @level_required(1)
    async def reload(self, ctx):
        
        await self.init.load_data(self.repos.guild_repository, self.repos.lobby_repository, self.repos.muted_repository, self.repos.malicious_urls_repository, self.repos.malicious_words_repository, self.repos.moderator_repository)
        await ctx.send(embed=Embed(description="Data Loaded"))
    
