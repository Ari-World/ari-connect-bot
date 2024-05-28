
import logging
import signal
import discord
import asyncio

import re

import aiohttp
from discord.ext import commands
from discord import ButtonStyle, Embed, Webhook

from enum import Enum

import schedule
# All code is moved into one cog due to adding cogs probelem.
# Issue is posted in  github

log = logging.getLogger("openworld.cog") 

class MessageTypes(Enum):
    REPLY = "REPLY"
    DELETE = "DELETE"
    UPDATE = "UPDATE"
    SEND = "SEND"

class OpenWorldServer(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.server_lobbies = None
        self.deleteMessageThreshold = 180
        self.controlChannel = 1230160106369318965
        self.cacheMessages = []

        self.openworldThanksMessage = ("Thanks for connecting to the Open World Server! \n\n"+
         "**Remember to:** \n" +
         "> Be respectful and considerate. \n" +
         "> Protect your privacy. \n" +
         "> Follow our community guidelines.\n" +
         "> No NSFW or Lewd content\n"+
         "> Keep the chats Family Friendly and Clean\n\n"
         "If you see anyone breaking the rules, use ` /report ` and our global mods will take care of it!\n\n"
         "- Once the message is sent, it cannot delete be deleted from other servers. Please be mindful of what you send")

        self.repositoryInitialize()
    # Caching data
    async def cog_load(self):
        self.guild_data  = await self.guild_repository.findAll()
        
        self.server_lobbies = await self.lobby_repository.findAll()

        self.muted_users = await self.muted_repository.findAll()

        self.malicious_urls = await self.malicious_urls_repository.findAll()

        self.malicious_words = await self.malicious_words_repository.findAll()
        
        self.initializeActivity()
    
    # Leading Scheduler for message
    def initializeActivity(self):
        """
        Initialize the activity field for each guild in self.guild_data.
        """
        log.info("Creating Cache data for message caching system")
        self.generateLobbySchedulerData()
   
    def delete_cache_message(self, source_id,lobbyName):
        for message in self.cacheMessages:
            if message["lobbyname"] == lobbyName:
                for source in message["messages"]:
                    if source["source"] == source_id:
                        message["messages"].remove(source)
                        return 
                    
    async def schedule_delete_cache_message(self, source_id, lobby_name):
        
        await asyncio.sleep(self.deleteMessageThreshold)

        self.delete_cache_message(source_id, lobby_name)
        log.info(f"Deleted message with source ID {source_id} from lobby {lobby_name} after {self.deleteMessageThreshold} seconds")


    def generateLobbySchedulerData(self):
        for lobby in self.server_lobbies:
            data =  {
                "lobbyname": lobby["lobbyname"],
                "messages": []
            }
            self.cacheMessages.append(data)

    def signal_handler(self, sig, frame):
        log.info('Received SIGINT, stopping scheduler...')
        self.stop()
        raise KeyboardInterrupt

    def stop(self):
        self.stop_scheduler = True
        schedule.clear()

    
    def repositoryInitialize(self):
        self.guild_repository = GuildRepository(self.bot.db)
        self.muted_repository = MutedRepository(self.bot.db)
        self.lobby_repository = LobbyRepository(self.bot.db)
        self.malicious_urls_repository = MaliciousURLRepository(self.bot.db)
        self.malicious_words_repository = MaliciousWordsRepository(self.bot.db)

    # ======================================================================================
    # Bot Commands
    # ======================================================================================
    @commands.command(name="addhooks")
    @commands.is_owner()
    async def addHooks(self,ctx :discord.ext.commands):
        msg = await ctx.send(embed = discord.Embed( description="Checking discord webhooks in channels"))
        
        changes = []
        errors = []
        for guild in self.guild_data:
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

            await self.guild_repository.update({
                "server_id": guild["server_id"],
                "channels": guild["channels"]
            })

        await msg.edit(embed = discord.Embed( description="Writing reports"))
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

    @commands.command(name="reloaddata")
    async def reload(self,ctx):
        await self.cog_load()
        await ctx.send(embed=Embed(
            description=" Data Loaded ",
        ))
             
    @commands.hybrid_command(name='connect', description='Link to Open World')
    @commands.has_permissions(kick_members=True)
    async def openworldlink(self, ctx, channel: discord.TextChannel):

        # ======================================================================================
        async def Validation(guild_id,channel_id):
            embed = Embed(
                description="Preparing ...",
                color=0x7289DA 
            )
            sent_message = await ctx.send(embed=embed)
            existing_guild = self.find_guild(guild_id, channel_id)
            if existing_guild:
                embed = Embed(
                    title=":no_entry: Your channel is already registered for Open World Chat",
                    description="Type `a!unlink` to unlink your Open World\n*This will only unlink from the Open World channel*",
                    color=0xFF0000  # Red color
                )
                await sent_message.edit(embed=embed)
                return {'message':'Failed', 'message_data':sent_message, 'server_name':None}
            else:
                return {'message':'Success', 'message_data':sent_message, 'server_name':existing_guild}
        
        async def SelectLobbies(guild_id,sent_message):
            # Getting lobbies and selecting available lobbies
            # ======================================================================================
            # Issue: handle the issue of user selecting the full lobbies
            # ======================================================================================
            async def SelectLobby():
                message = await self.show_lobbies_embed(ctx,"Available Lobbies", description=None)
                lobby =ConnectDropDown(ctx.message.author,self.server_lobbies)
                
                message_drp = await ctx.send(view=lobby)
                try:
                    await asyncio.wait_for(lobby.wait(), timeout=60)
                except asyncio.TimeoutError:
                    await ctx.send("You didn't respond within the specified time.")
                    await message.delete()
                    await message_drp.delete()
                    raise Exception("")
                
                await message.delete()
                await message_drp.delete()
                return lobby.lobby

            async def AboutLobby(about):
                for lobby in self.server_lobbies:
                    if lobby["lobbyname"] == about:
                        description = lobby["description"]
                # This is a duplicate from current_lobby command
                guilds = self.getAllGuildUnderLobby(about)
                data = ""
                x = 1
                if guilds:
                    for guild in guilds:
                        text = f"**{x}**) **{guild['server_name']}**"
                        data += text + "\n\n"
                        x += 1
                else:
                    data = "There's no guild connected to this lobby"
                choice = Choice(ctx.message.author)

                embed = Embed(
                    title= about,
                    description=description,
                    color=0x7289DA
                )

                
                embed.add_field(name="Guilds",value=data)
                await sent_message.edit(embed = embed)
                msg_choice = await ctx.send(view=choice)
                
                try:
                    await asyncio.wait_for(choice.wait(), timeout=60)
                except asyncio.TimeoutError:
                    await ctx.send("You didn't respond within the specified time.")
                    await msg_choice.delete()
                    await sent_message.delete()
                    raise Exception("")
                
                await msg_choice.delete()
                return choice.value
            
            # ======================================================================================
            # Menu Manager
            
            while True:
                lobby = await SelectLobby()
                choice = await AboutLobby(lobby)
               
                if choice is True:
                    return {'message':'Success', 'message_data':sent_message, 'lobby': lobby} 
        async def CheckLobby(sent_message, lobby):
            message = "Full"

            lobbyData = await self.getAllLobby()
            
            limit = None  # Define limit variable
            for data in self.server_lobbies:
                limit = data.get("limit")  # Use .get() to avoid KeyError if "limit" is not present
                if limit is not None:
                    break
            
            if limit is not None:  # Proceed only if limit is found
                for x in lobbyData:
                    if x.get("name") == lobby and x.get("connection", 0) < limit:  # Adjust condition check
                        message = "Available"
                        break

            return {'message': message, 'message_data':sent_message} 
        async def Login(guild_id, sent_message):  
            # Logging in process
            embed = Embed(
                description="Logging in ...",
                color=0x7289DA 
            )
            await sent_message.edit(embed=embed)
            await asyncio.sleep(1)
            embed.description = "Linking into Open World Server..."
            await sent_message.edit(embed=embed)
            await asyncio.sleep(1)
            embed.description = f"Confirming Connection with World - `{guild_id}`..."
            await sent_message.edit(embed=embed)
            await asyncio.sleep(1)
            embed.description = f"Fetching Data from World - `{guild_id}`..."
            await sent_message.edit(embed=embed)
            await asyncio.sleep(1)

            return {'message':'Success', 'message_data':sent_message} 
        
        async def CreateConnection(lobby, sent_message, guild_name):
            # Create Connection
            # now connect
            await self.create_guild_document(guild_id, channel, guild_name, lobby)
            embed = Embed(
                description=f':white_check_mark: **LINK START!! You are now connected to {lobby}**',
                color=0x7289DA 
            )
            await sent_message.edit(embed=embed)
            await asyncio.sleep(1)
            # sends a successful message
            embed = Embed(
                title="Thank you for linking with Open World Server!",
                description= self.openworldThanksMessage,
                color=0x00FF00 
            )
            message = await ctx.send(embed=embed)
            await message.add_reaction('✅')
            return {'message':'Success', 'message_data':sent_message} 
        
        def isFailed(response):
            if(response['message'] == "Failed"):
                raise Exception("")
            else:
                return response
            
        async def Sequence(guild_id, channel_id, guild_name):
            
            while True:
                response = isFailed(await Validation(guild_id, channel_id))
   
                responseWithlobby = isFailed(await SelectLobbies(guild_id, response['message_data']))

                response = isFailed(await CheckLobby(response['message_data'], responseWithlobby["lobby"]))
                if response["message"] == "Available":
                    break
            response = isFailed(await Login(guild_id, responseWithlobby['message_data']))
            
            response = isFailed(await CreateConnection(responseWithlobby['lobby'], response['message_data'], guild_name))
        # ======================================================================================
        # Runtime Manager

        guild_id = ctx.guild.id
        channel_id = channel.id
        guild_name = ctx.guild.name

        # Sequence 
        await Sequence(guild_id, channel_id, guild_name)

    @commands.hybrid_command(name='unlink', description='Unlink from Open World')
    @commands.has_permissions(kick_members=True)
    async def openworldunlink(self, ctx):
        # Initialize needed data
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        
        # checks if the channel exists in the database
        existing_guild = self.find_guild(guild_id, channel_id)
        if existing_guild:
            # if it does exists, delete it from database
            await self.delete_guild_document(guild_id, channel_id)
            await ctx.send(
                embed=discord.Embed(
                    description=":white_check_mark: **Unlinked from Open World Chat**",
                    color= 0x00FF00)
                )
        else:
            # else if doesnt 
            await ctx.send(
                embed=discord.Embed(
                    description=":no_entry: **Your channel is not registered for Open World Chat**",
                    color= 0xFF0000)
                    )

    def contains_malicious_url(self, content):
        if self.malicious_urls and self.malicious_words:
            for url in self.malicious_urls:
                if re.search(url['content'],content, re.IGNORECASE):
                    return True
                
            for word in self.malicious_words:
                if word['content'].lower() in content.lower():
                    return True
            
        return False

    @commands.Cog.listener()
    async def on_message_delete(self, message:discord.Message):
        if message.author.bot:  # Check if the author of the deleted message is the bot
            return

        guild_id = message.guild.id
        channel_id = message.channel.id
        
        guild_document = self.find_guild(guild_id, channel_id)

        # This mainly checks if this is the global chat or not
        if not guild_document:
            return
        
        await self.validate_webhook_channel(message, guild_document, channel_id, MessageTypes.DELETE)

    @commands.Cog.listener()
    async def on_message_edit(self,before, after):
        if before.author.bot:
            return
        

        guild_id = before.guild.id
        channel_id = before.channel.id
        
        guild_document = self.find_guild(guild_id, channel_id)

        # This mainly checks if this is the global chat or not
        if not guild_document:
            return

        
        await self.validate_webhook_channel(after, guild_document, channel_id, MessageTypes.UPDATE)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        
        if message.content.startswith(self.bot.command_prefix) or message.author.bot:
            return

        guild_id = message.guild.id
        channel_id = message.channel.id
        
        guild_document = self.find_guild(guild_id, channel_id)

        # This mainly checks if this is the global chat or not
        if not guild_document:
            return
        
        sender = self.bot.get_user(message.author.id)
        #  TODO: Improve Security
        muted = self.isUserBlackListed( message.author.id)
        # Checks if the user is blacklisted
        if muted:
            await message.delete()
            await sender.send(embed=Embed(description=f"You have been muted for {muted["reason"]}"))
            return
        # Checks if the message is harmfulll
        if self.contains_malicious_url(message.content):
            await message.delete()
            await message.author.send(embed = Embed( description= "Your message contains malicious content. Please refrain from using inappropriate language or sharing harmful links."))    
            await self.log_report(message, "Sending Malicious Content")
            return
        
        if(message.type == discord.MessageType.reply):
            messageType = MessageTypes.REPLY
        else:
            messageType = MessageTypes.SEND
        # All checks done, Process the message

        await self.validate_webhook_channel(message, guild_document, channel_id, messageType)

    async def validate_webhook_channel(self, message: discord.Message, guild_document, channel_id, messageType: MessageTypes):
        # This function determines if where lobby should the message be sent     
        for channel in guild_document["channels"]:
            if channel["channel_id"] == channel_id and channel["webhook"]:    
                await self.send_to_matching_lobbies(message, channel['lobby_name'], channel_id, messageType)
            elif not channel["webhook"]:
                await message.channel.send("Re-register this channel for webhook registration")

    async def send_to_matching_lobbies(self, message: discord.Message, lobby_name, channel_id, messageType: MessageTypes ):
        # Prepare messagesData
        if messageType == MessageTypes.REPLY or messageType == MessageTypes.SEND:
            messagesData = {"source": message.id, "channel": message.channel.id,"webhooksent": []}
            embed = None
            source_data = None

            if message.reference and messageType == MessageTypes.REPLY:
                embed = await self.prepare_reply_embed(message, lobby_name)

        if messageType == MessageTypes.DELETE or messageType == MessageTypes.UPDATE:
            source_data = self.find_source_data(message.id, lobby_name)

            combined_ids = [{"channel": source_data["channel"], "messageId": source_data["source"]}]
            combined_ids.extend(data for data in source_data["webhooksent"] if data["messageId"] != message.id)
        
        async with aiohttp.ClientSession() as session:
            tasks = []

            for document in self.guild_data:
                channels = document["channels"]
                for channel in channels:
                    # Checks if its not the guild and the channels via id basically filtered out the current channel
                    if channel["channel_id"] != channel_id and channel["lobby_name"] == lobby_name:
                        
                        # webhook = self.create_webhook(channel["webhook"], session, messageType)
                        webhook  = Webhook.from_url(channel["webhook"], session=session)

                        if messageType == MessageTypes.SEND:
                            tasks.append(self.process_message(webhook,  message, messagesData))
                        elif messageType == MessageTypes.REPLY: # Remove and combined_ids
                            # Reply Jump message
                            # view = await self.handle_reply(combined_ids, channel["channel_id"] )
                            tasks.append( self.process_message(webhook, message, messagesData, embed))
                        elif messageType == MessageTypes.DELETE and combined_ids:
                            relative_message : discord.Message = await self.find_messageID(channel["channel_id"],combined_ids,)
                            tasks.append( self.process_edit_message(message,webhook, relative_message.id, messageType))
                        elif messageType == MessageTypes.UPDATE and combined_ids:
                            relative_message : discord.Message = await self.find_messageID(channel["channel_id"],combined_ids)
                            tasks.append( self.process_edit_message(message,webhook, relative_message.id, messageType))

            await asyncio.gather(*tasks)
            if messageType == MessageTypes.REPLY or messageType == MessageTypes.SEND:
                await self.cache_message(lobby_name, messagesData)

    async def process_message(self, webhook : Webhook, message : discord.Message, messagesData, embed = None):
        try:
            allowed_mentions = discord.AllowedMentions(everyone=False, users=False, roles=False)

            files = [await attachment.to_file() for attachment in message.attachments]
            
            # Check if the message contains a sticker
            if message.stickers and not embed:  # If there's a sticker and embed argument is not provided
                sticker = message.stickers[0]  # Assuming there's only one sticker in the message
                embed = discord.Embed()
                embed.set_image(url=sticker.url)
                content = message.content
            else:
                embed = embed  # Use provided embed
                content = message.content  # Use message content
            wmsg : discord.WebhookMessage  = await webhook.send(
                content=  content,
                username=f"{message.author.global_name} || {message.guild.name}",
                avatar_url=message.author.avatar.url,
                allowed_mentions=allowed_mentions,
                files=files,
                embed = embed,
                wait=True
            )
            messagesData["webhooksent"].append({ "channel": wmsg.channel.id ,"messageId" : wmsg.id})

            # This is jump command for the button view 
            # it needs to be this way because its partial view which need to have a state
            # if view and embed:
            #     wmsg : discord.WebhookMessage  = await webhook.send(
            #         content=  content,
            #         username=f"{message.author.global_name} || {message.guild.name}",
            #         avatar_url=message.author.avatar.url,
            #         allowed_mentions=allowed_mentions,
            #         files=files,
            #         embed = embed,
            #         view = view,
            #         wait=True
            #     )
            # else:
            #     wmsg : discord.WebhookMessage  = await webhook.send(
            #         content=  content,
            #         username=f"{message.author.global_name} || {message.guild.name}",
            #         avatar_url=message.author.avatar.url,
            #         allowed_mentions=allowed_mentions,
            #         files=files,
            #         embed = embed,
            #         wait=True
            #     )
        except KeyError as k:
            log.warning(k)
        except Exception as e:
            log.warning(e)
    
    async def process_edit_message(self, message: discord.Message, webhook : Webhook, message_id, messageType):
        try:
            content = "*[message deleted]*"
            if messageType == MessageTypes.UPDATE:
                 content = message.content

            await webhook.edit_message(
                message_id,
                content = content,
            )
        except Exception as e:
            log.warning(f"Failed to edit message {message.id}: {e}")

   
    async def find_messageID(self, target_channel_id,combined_ids):
        channel = self.bot.get_channel(target_channel_id)
        fetch_tasks = [self.try_fetch_message(target_channel_id, data, channel) for data in combined_ids]
        fetched_messages = await asyncio.gather(*fetch_tasks)
        replied_message = next((msg for msg in fetched_messages if msg is not None), None)
        return replied_message
    
    async def handle_reply(self, combined_ids, target_channel_id):
        """Handles reply Jump Button feature

            Parameters:
                combined_ids : list[ dict ]
                target_channel_id : int
            
            Returns:
                view: Discord.view, and None if replied_message is None
        """
        log.info("Getting the message id")
        channel = self.bot.get_channel(target_channel_id)
        fetch_tasks = [self.try_fetch_message(target_channel_id, data, channel) for data in combined_ids]
        fetched_messages = await asyncio.gather(*fetch_tasks)
        replied_message = next((msg for msg in fetched_messages if msg is not None), None)
        log.info("Message found")
        log.info(replied_message)
        if replied_message:
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Jump to message", style=discord.ButtonStyle.link, url=replied_message.jump_url))
            return view
        else:
            log.warning("There's no replied message found")
            return None

    def create_webhook(self, webhook_url, session, messageType):
        if messageType == MessageTypes.REPLY:
            match = re.match(r'https://discord.com/api/webhooks/(\d+)/(.+)', webhook_url)
            if not match:
                raise ValueError("Invalid webhook URL format")
            webhook_id, webhook_token = match.groups()
            return discord.Webhook.partial(id=int(webhook_id), token=webhook_token, session=session, client=self.bot)
        else:
            return discord.Webhook.from_url(webhook_url, session=session)
    
    async def try_fetch_message(self, target_channel_id, data, channel):
        try:
            if data["channel"] == target_channel_id:
                return await channel.fetch_message(data["messageId"])
        except discord.NotFound:
            return None
             
    async def prepare_reply_embed(self, message : discord.Message, lobby_name):
        replied_message = await message.channel.fetch_message(message.reference.message_id)
        embed = self.create_embed_for_message(replied_message)

        # source_data = self.find_source_data(replied_message.id, lobby_name)

        # combined_ids = [{"channel": source_data["channel"], "messageId": source_data["source"]}]
        # combined_ids.extend(data for data in source_data["webhooksent"] if data["messageId"] != replied_message.id)

        # return source_data, embed
        return embed

    def create_embed_for_message(self,replied_message : discord.Message):
        embed = discord.Embed(description=f"{replied_message.content}", color=0xff69b4)
        if replied_message.webhook_id:
            author_name = replied_message.author.name
        else:
            author_name = f"{replied_message.author.global_name} || {replied_message.guild.name}"
        embed.set_author(name=author_name, icon_url=replied_message.author.avatar.url)

        for attachment in replied_message.attachments:
            if attachment.filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'webp')):
                embed.set_image(url=attachment.url)
        
        return embed
    
    def find_source_data(self, message_id, lobby_name):
        for data in self.cacheMessages:
            if data["lobbyname"] == lobby_name:
                for messages in data["messages"]:
                    if messages["source"] == message_id:
                        return messages
                    for webhook in messages["webhooksent"]:
                        if webhook["messageId"] == message_id:
                            return messages
        return None
    
    async def cache_message(self, lobby_name, messagesData):
        for data in self.cacheMessages:
            if data["lobbyname"] == lobby_name:
                data["messages"].append(messagesData)
                await self.schedule_delete_cache_message(messagesData["source"], lobby_name)
    
    async def get_lobby_count(self, lobby_name: str) -> int:
        count = 0
        async for document in self.bot.db.guilds_collection.find():
            channels = document.get("channels", [])
            for channel in channels:
                if channel.get("lobby_name") == lobby_name:
                    count += 1
        return count
    
    #Get Current Lobby
    @commands.hybrid_command(name='current', description='Current Lobby description')
    async def current_lobby(self, ctx):
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id

        guild_document = self.find_guild(guild_id,channel_id)

        if self.server_lobbies:
            if guild_document:

                lobby = guild_document.get("channels",[])
            
                for channel in lobby:
                    if channel["channel_id"] == channel_id:
                        lobby_name = channel['lobby_name']
                        limit = self.get_limit_server_lobby(lobby_name)
                        description = None
                        guilds =  self.getAllGuildUnderLobby(channel['lobby_name'])
                        connection = await self.get_lobby_count(channel['lobby_name'])
                        # Lobby Data
                        for lobby in self.server_lobbies:
                            if lobby["lobbyname"] == lobby_name:
                                description = lobby["description"]
                        data = ""
                        x = 1

                        if guilds:
                            for guild in guilds:
                                
                                text = f"**{x}**) **{guild['server_name']}**"
                                data += text + "\n\n"
                                x += 1
                        else:
                            data = "There's no guild connected to this lobby"

                        embed = Embed(
                            title= f"{channel['lobby_name']} - {connection}/{limit}",
                            description= description,
                            color= 0xFFC0CB 
                        )
                        embed.add_field(name="Connected:", value = data)
                        return await ctx.send(embed=embed)
            else:
                embed = Embed(
                    description=f":no_entry: **Your channel is not registered for Open World Chat**",
                    color=0xFFC0CB
                )
                
                return await ctx.send(embed=embed)

    @commands.hybrid_command(name='lobbies', description='Current Lobby description')
    async def show_lobbies(self, ctx):
        await self.show_lobbies_embed(ctx, title="Lobbies Online",description="Some description to add")

    async def show_lobbies_embed(self, ctx, title ,description):
        lobby_data = await self.getAllLobby()
        formatted_data = ""

        for data in lobby_data:
            limit = self.get_limit_server_lobby(data["name"])
            connection = data['connection']
            
            if connection > limit - 5:
                # If the number of connections is close to the limit, display 🔴
                text = f"\n🔴 **{data['name']}**\n {connection}/{limit} guilds connected"
            elif connection > limit - 10:
                # If the number of connections is moderate, display 🟠
                text = f"\n🟠 **{data['name']}**\n {connection}/{limit} guilds connected"
            else:
                # If the number of connections is low, display 🟢
                text = f"\n🟢 **{data['name']}**\n {connection}/{limit} guilds connected"
            
            formatted_data += text + "\n"

        embed = Embed(
            title= title,
            description= description,
            color=0x7289DA 
        )
        embed.add_field(name="Public Lobbies",value=formatted_data)
        return await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='switch', description='Switch to a different server lobby')
    @commands.has_permissions(kick_members=True)
    async def switch_lobby(self, ctx):

        async def Menu():
            async def ConfirmLeave():
                embed = Embed(
                    description= ":warning: **Are you sure do you want to leave?**",
                    color = 0x7289DA 
                )
                message = await ctx.send(embed=embed)
                
                choice = Choice(ctx.message.author)
                msg_choice = await ctx.send(view=choice)

                try:
                    await asyncio.wait_for(choice.wait(), timeout=60)
                except asyncio.TimeoutError:
                    await ctx.send("You didn't respond within the specified time.")
                    await msg_choice.delete()
                    await message.delete()
                    raise Exception("")
                
                await message.delete()
                await msg_choice.delete()
                return choice.value
            
            async def SelectLobby():
                message = await self.show_lobbies_embed(ctx,"Available Lobbies", description=None)
                lobby = ConnectDropDown(ctx.message.author,self.server_lobbies)
                message_drop = await ctx.send(view=lobby)
                try:
                    await asyncio.wait_for(lobby.wait(), timeout=60)
                except asyncio.TimeoutError:
                    await ctx.send("You didn't respond within the specified time.")
                    await message_drop.delete()
                    await message.delete()
                    raise Exception("")
                

                await message_drop.delete()
                return {"lobby": lobby.lobby, "message":message}
            # ======================================================================================
            # Menu Manager

            while True:
                choice = await ConfirmLeave()
                if choice == False:
                    return {'message': 'Failed', 'message_data': None, "lobby": None}
                response = await SelectLobby()
                
                if response['lobby']:
                    return {'message': 'Success', 'message_data': response["message"], "lobby":  response['lobby']}



        async def Validation(guild_id,channel_id):

            existing_guild = self.find_guild(guild_id, channel_id)

            if existing_guild:
                channels = existing_guild.get("channels",[])
                for channel in channels:
                    # Checks if user is in the lobby

                    if channel['channel_id'] == channel_id:
                        return {'message': 'Success' , 'channel': channel}
            else:
                embed = Embed( 
                    description=f":no_entry: **Your channel is not registered for Open World Chat**",
                    color=0x7289DA 
                )
                await ctx.send(embed=embed)
                return {'message': 'Failed', 'channel': None }
            
        # Might change this to a drop down function
        async def updateLobbyConnection(guild_id, channel_id, message, lobby):
            
            await self.update_guild_lobby(guild_id, channel_id, lobby)

            embed = Embed(
                description=f":white_check_mark: **You have switched to {lobby}**",
                color=0x7289DA 
            )

            await message.edit(embed=embed)

        def isFailed(response):
            if(response['message'] == "Failed"):
                raise Exception("")
            else:
                return response
            
        async def Sequence(guild_id,channel_id):
            
            channel = isFailed(await Validation(guild_id, channel_id))
            
            lobby = isFailed(await Menu())

            if channel['channel']['lobby_name'] == lobby['lobby']:
                await ctx.send(
                    embed = Embed(
                        description= f"<:no:1226959471910191154> **You're already in {lobby["lobby"]}**"
                    )
                )
            else:
                await updateLobbyConnection(guild_id, channel_id, lobby['message_data'] , lobby["lobby"])
        # ======================================================================================
        # Run Time Manager
        # ======================================================================================
        # Potential Issues:
        # - Chat still goes even during switching
        #  
        # ======================================================================================
        
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id

        # Sequence
        await Sequence(guild_id,channel_id)

    # ======================================================================================
    # Fuctions used for the commands
    # ======================================================================================
    def get_limit_server_lobby(self, name):
        for lobby in self.server_lobbies:
            if lobby["lobbyname"] == name:
                return lobby["limit"]


    def isUserBlackListed(self,id):
        if self.muted_users:
            for user in self.muted_users:
                if user["id"] == id:
                    return user
        return None


    def find_guild(self, guild_id: int, channel_id: int, tag: str = None):
        """
        Find a guild in the cached guild data by guild_id and channel_id.
        
        Args:
            guild_id (int): The ID of the guild to find.
            channel_id (int): The ID of the channel to find within the guild.
        
        Returns:
            dict or None: The guild data if found, otherwise None.
        """
        for guild in self.guild_data:  
            if guild["server_id"] == guild_id:  
                channels = guild.get("channels", [])
                for channel in channels: 
                    if channel["channel_id"] == channel_id:
                        return guild  
        return None  

    def findCachedLobby(self, lobbyName):
        """
            Finds the cache message 

            Args:
                lobbyname (str) : The name of the specified lobby
            
            Returns:
                dict : the cache memory if found, otherwise none
        """

        for data in self.cacheMessages:
            if lobbyName == data["lobbyname"]:
                return data
        
        return None
            
    async def log_report(self,message,reason):
        guild = self.bot.get_guild(939025934483357766)
        target_channel = guild.get_channel(1230069779071762473)

        embed = Embed(
            title="Detected by system",
            description= f"**User {message.author.name} has been flagged due {reason}**\n\n**Message:**\n\n {message.content}"
        )
        embed.set_footer(text = f"userid {message.author.id}")
        await target_channel.send(embed=embed)        


    def get_allowed_mentions(self, message, include_author=True):
        allowed_mentions = discord.AllowedMentions.none()

        return allowed_mentions   
    
    # TODO: Reduce Database usage and use the memory data than database queries
    async def getAllLobby(self):
        lobby_data = {lobby["lobbyname"]: 0 for lobby in self.server_lobbies}
        
        for document in await self.guild_data:
            channels = document["channels"]
            
            for channel in channels:
                lobby_name = channel['lobby_name']
                
                if lobby_name in lobby_data:  # Check if the lobby is in the lobby_data dictionary

                    lobby_data[lobby_name] += 1  # Increment count for the lobby

        formatted_data = [{"name": lobby, "connection": count} for lobby, count in lobby_data.items()]
        
        sorted_data = sorted(formatted_data, key=lambda x: x["connection"], reverse=True)
    
        return sorted_data

    # TODO: Reduce Database usage and use the memory data than database queries
    async def getLobbyConnections(self,lobby_name,current_guild=None):
        if current_guild is not None:
            filter_query = {"_id": {"$ne": current_guild}, "channels.lobby_name": lobby_name}
        else:
            filter_query = {"channels.lobby_name": lobby_name}  # Filter by lobby_name if current_guild is None
        lobby_connection_count = 0
        self.guild_data
        async for document in await self.guild_repository.findFilter(filter_query):
            channels = document.get("channels", [])
            
            for channel in channels:
                if channel['lobby_name'] == lobby_name:
                    lobby_connection_count += 1

        return {"name": lobby_name, "connection": lobby_connection_count}
    
    # Scuffed Code
    def getAllGuildUnderLobby(self, lobby_name):
        guilds = []
        for document in self.guild_data:
            channels = document["channels"]
            for channel in channels:
                if lobby_name == channel["lobby_name"]:
                    guilds.append(document)
        return guilds
    
    async def create_guild_document(self, guild_id, channel : discord.TextChannel, server_name, lobby_name):
        """
        Create or update a guild document in the database and cache.
        
        Args:
            guild_id (int): The ID of the guild.
            channel (discord.TextChannel): The Discord text channel object.
            server_name (str): The name of the server.
            lobby_name (str): The name of the lobby.
        
        Returns:
            bool: True if the operation is successful, False otherwise.
        """

        channel_id = channel.id  
        guild_document = None
        for guild in self.guild_data:  
            if guild["server_id"] == guild_id:  
                guild_document = guild
        
        webhook = await channel.create_webhook(name=server_name)
        if guild_document:

            channels = guild_document["channels"]  # Get the channels of the guild
            if any(ch["channel_id"] == channel_id for ch in channels):  # Check if the channel already exists
                return False  # Return False if the channel already exists

            channels.append({"channel_id": channel_id, "lobby_name": lobby_name, "webhook": webhook.url, "activity": False})  # Add the new channel
            update_successful = await self.guild_repository.update({
                "server_id": guild_id,
                "channels": channels
            })
           
            if update_successful:
                for guild in self.guild_data:
                    if guild["server_id"] == guild_id:
                        guild["channels"] = channels
                        for channel in guild["channels"]:
                            if "activity" not in channel:
                                channel["activity"] = False



        else:
            insertion_successful = await self.guild_repository.create({
                "server_id": guild_id,
                "server_name": server_name,
                "channels": [{"channel_id": channel_id, "lobby_name": lobby_name, "webhook": webhook.url, "activity": False}]
            })

            if insertion_successful:
                # Add the new guild to the cache only if the database insertion was successful
                self.guild_data.append({
                    "server_id": guild_id,
                    "server_name": server_name,
                    "channels": [{"channel_id": channel_id, "lobby_name": lobby_name, "webhook": webhook.url, "activity": False}],
                })

        return True

    async def update_guild_lobby(self, guild_id: int, channel_id: int, lobby_name: str):
        guild_document = None
        for guild in self.guild_data:  
            if guild["server_id"] == guild_id:  
                guild_document = guild
        if guild_document:
            channels = guild_document["channels"] 

            # Get's all the channel and change the lobby name then break
            for channel in channels:
                if channel["channel_id"] == channel_id:
                    channel["lobby_name"] = lobby_name
                    break
            update_successful = await self.guild_repository.update({
                "server_id": guild_id,
                "channels": channels
            })
           
            if update_successful:
                for guild in self.guild_data:
                    if guild["server_id"] == guild_id:
                        guild["channels"] = channels
                        for channel in guild["channels"]:
                            if "activity" not in channel:
                                channel["activity"] = False
     
    async def delete_guild_document(self, guild_id: int, channel_id: int):
       
        guild_document = None
        for guild in self.guild_data:  
            if guild["server_id"] == guild_id:  
                guild_document = guild
        # If data exists
        if guild_document:
            # Get all channels within the guild
            channels = guild_document["channels"]

            # Find the channel to delete and get its webhook
            channel_to_delete = next((channel for channel in channels if channel["channel_id"] == channel_id), None)
            
            if channel_to_delete:
                # Unregister the webhook
                discord_channel = self.bot.get_channel(channel_id)
                if discord_channel:
                    webhooks = await discord_channel.webhooks()
                    for webhook in webhooks:
                        if webhook.id == channel_to_delete["webhook"]:
                            await webhook.delete()
                            break

                # Remove the channel from the list
                channels = [channel for channel in channels if channel["channel_id"] != channel_id]

                # If there are still channels left, update the data
                if channels:
                    update_successful = await self.guild_repository.update({
                        "server_id": guild_id,
                        "channels": channels
                    })
                
                    if update_successful:
                        for guild in self.guild_data:
                            if guild["server_id"] == guild_id:
                                guild["channels"] = channels
                                for channel in guild["channels"]:
                                    if "activity" not in channel:
                                        channel["activity"] = False

                else:
                    # Otherwise, delete the guild document
                    result = await self.bot.db.guilds_collection.delete_one({"server_id": guild_id})
                    if result:
                        self.guild_data = [guild for guild in self.guild_data if guild["server_id"] != guild_id]
    

    # ======================================================================================
    # Moderation
    # ======================================================================================
    @commands.hybrid_command(name="report",description="Report a user for misbehaving, and attach a picture for proff")
    async def report_user(self, ctx,username, reason, attacment:discord.Attachment):
        if not attacment:
            await ctx.send(embed=discord.Embed(description=f"Please provide a picture"))

        await ctx.send(embed=discord.Embed(description=f"User has been reported"))
        await self.log_report(username,ctx.author.name,reason,attacment)

    @commands.command(name="moderation")
    #@commands.has_role("@Ari Global Mod")
    async def GcCommands(self,ctx):
        embed = discord.Embed(
            title="Moderation Commands",
            description= (
                "Commands aren't registered as slash commands for limited visibility"
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
            
            "`a!add_badlink` \"word\" - Add word to filter\n"
            "`a!remove_links` \"word\" - Remove word to the list\n\n"


            "`a!add_badwords` \"word\" - Add word to filter\n"
            "`a!remove_badwords` \"word\" - Remove word to the list\n\n"
            
            "**Deprecated Commands**\n"
            "`a!reload data`- reload data in the cache (still working)\n"
            "Reason: Removed because its already automated, beware to reload data unless necessary causes database query overload"
        ), inline=False)
        await ctx.send(embed = embed)
        
    @commands.command(name="listmuted")
    async def getAllMuted(self,ctx):
        channel = ctx.guild.get_channel(self.controlChannel)
        
        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return
        
        format_data = ""
        if self.muted_users:
            x=1
            for data in self.muted_users:
                text = f"{str(x)}) **{data['name']} || {data['id']}**\nReason : {data['reason']}"
                format_data += text + "\n"
                x += 1

        embed = discord.Embed(
            title="Muted List",
            description=format_data
        )
        await ctx.send(embed=embed)

    # TODO: Improve Embed
    @commands.command(name="listbadwords")
    async def getAllBadwords(self,ctx):
        channel = ctx.guild.get_channel(self.controlChannel)
        
        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return
        
        format_data = ""
        if self.malicious_words:
            x=1
            for data in self.malicious_words:
                text = f"{str(x)}) {data["content"]} "
                format_data += text + "\n"
                x += 1

        embed = discord.Embed(
            title="Banned Words",
            description=format_data
        )
        await ctx.send(embed=embed)

    # TODO: Improve Embed
    @commands.command(name="listbadurls")
    async def getAllBadUrls(self,ctx):
        channel = ctx.guild.get_channel(self.controlChannel)
        
        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return
        
        format_data = ""
        if self.malicious_urls:
            x=1
            for data in self.malicious_urls:
                text = f"{str(x)}) {data["content"]} "
                format_data += text + "\n"
                x += 1

        embed = discord.Embed(
            title="Banned Urls",
            description=format_data
        )
        await ctx.send(embed=embed)

    @commands.command(name='mute')
    #@commands.has_role("@Ari Global Mod")
    async def MuteUser(self, ctx, id : int,reason:str):
        user = await self.bot.fetch_user(id)
        channel = ctx.guild.get_channel(self.controlChannel)
        
        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return
        
        if user.bot or not user:
            await ctx.send(embed=discord.Embed( description=" No User Found"))
            return
        
        data = {
            "id": user.id,
            "name" : user.name,
            "reason": reason,
            "mutedBy" : ctx.message.author.name
        }
        await self.muted_repository.create(data)
        self.muted_users.append(data)
        await ctx.send(embed=discord.Embed( description=f" User {user.id} ({user.name}) has been muted"))

    @commands.command(name='unmute')
    #@commands.has_role("@Ari Global Mod")
    async def UnMuteUser(self, ctx, id: int):
        user = await self.bot.fetch_user(id)
        channel = ctx.guild.get_channel(self.controlChannel)
        exists = await self.muted_repository.findOne(id)

        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return
        
        if user.bot or not user or not exists:
            await ctx.send(embed=discord.Embed( description=" No User Found"))
            return
        
          
        sender = self.bot.get_user(id) 
        await self.muted_repository.delete(user.id)
        self.muted_users.remove(exists)
        await sender.send(embed=discord.Embed(description=f"You have been unmuted from Global Chat!\n\n Welcome back! try to not get reported again"))
        await ctx.send(embed=discord.Embed( description=f" User {user.id} ({user.name}) has been unmuted"))
          
    @commands.hybrid_command(name='add_lobby')
    @commands.is_owner()
    async def AddLobbies(self, ctx, name:str, description: str ,limit:int):
        channel = ctx.guild.get_channel(self.controlChannel)
        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return  
        
        if self.server_lobbies:
            for x in self.server_lobbies:
                if name == x['lobbyname']:
                    await ctx.send(embed=discord.Embed( description="Lobby Exists"))
                    return

        data = {
            "lobbyname":name,
            "description": description,
            "limit":limit
        }
        await self.lobby_repository.create(data)
        self.server_lobbies.append(data)
        await ctx.send(embed=discord.Embed( description=f" Lobby {name} has been newly added"))
    
    @commands.command(name='add_badlink')
    #@commands.is_owner()
    async def AddblockLinks(self, ctx, content):
        channel = ctx.guild.get_channel(self.controlChannel)
        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return
        self.malicious_urls.append(content)
        await self.malicious_urls_repository.create(content)
        await ctx.send(embed = discord.Embed(
            description= f"Content has been added to list"
        ))
    @commands.command(name='remove_links')
    async def RemoveBlockLinks(self, ctx, content):
        channel = ctx.guild.get_channel(self.controlChannel)
       
        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return

        exists = await self.malicious_urls_repository.findOne(content)
 
        if exists:
            await self.muted_repository.delete(exists["content"])
            self.malicious_urls.remove(exists)
            await ctx.send(embed=discord.Embed( description=f" {exists["content"]} has been removed to the list"))
        else:    
            await ctx.send(embed=discord.Embed( description=f"{content}not found in the list"))

    @commands.command(name='add_badwords')
    #@commands.is_owner()
    async def Addblockwords(self,ctx, content):
        channel = ctx.guild.get_channel(self.controlChannel)
        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return
        self.malicious_words.append(content)
        await self.malicious_words_repository.create(content)
        await ctx.send(embed = discord.Embed(
            description= f"Content has been added to list"
        ))
    
    @commands.command(name='remove_badwords')
    async def RemoveBlockWorlds(self, ctx, content):
        channel = ctx.guild.get_channel(self.controlChannel)

        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return
        
        exists = await self.malicious_words_repository.findOne(content)
 
        if exists:
            await self.muted_repository.delete(exists["content"])
            self.malicious_words.remove(exists)
            await ctx.send(embed=discord.Embed( description=f" {exists["content"]} has been removed to the list"))
        else:    
            await ctx.send(embed=discord.Embed( description=f"{content}not found in the list"))
          

    async def log_report(self,name,reportedBy,reason, attachments):
        guild = self.bot.get_guild(939025934483357766)
        target_channel = guild.get_channel(975254983559766086)

        embed = discord.Embed(
            title="Reported",
            description= f"**User {name} has reported by {reportedBy}**"
        )
        embed.set_footer(text = f"reported by {reportedBy}")
        
        if not isinstance(attachments, list):
           attachments = [attachments]

        for index, attachment in enumerate(attachments, start=1):
            embed.add_field(name=f"Proof {index}", value=attachment.url)
        
        await target_channel.send(embed=embed)


        
async def setup(bot:commands.Bot):
    await bot.add_cog(OpenWorldServer(bot))



class MaliciousURLRepository():
    def __init__(self, db):
        self.collection = db.malurl_collection()

    async def findAll(self):
            cursor = self.collection.find()
            return await cursor.to_list(length=None)
        
    async def findOne(self,data):
        return await self.collection.find_one({"content" : data})
    
    async def create(self, data):
        if await self.findOne(data): 
            return None
        await self.collection.insert_one({
            "content" : data
        })
        return {
            "content" : data
        }
    
    async def delete(self,data):
        if await self.findOne(data): 
            return await self.collection.delete_one({
                "content" : data
            })
        else:
            return None

class MutedRepository():
    def __init__(self, db):
        self.collection = db.muted_collection()

    async def findAll(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)
    
    async def findOne(self,id):
        return await self.collection.find_one({"id":id})
    
    async def create(self, data):
        return await self.collection.insert_one({
            "id": data["id"],
            "name":data["name"],
            "reason": data["reason"]
        })
    
    async def delete(self,id):
        return await self.collection.delete_one({
            "id": id,
        })
        

class MaliciousWordsRepository():
    def __init__(self, db):
        self.collection = db.malword_collection()

    async def findAll(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)
    
    async def findOne(self,data):
        return await self.collection.find_one({"content" : data})
    
    async def create(self, data):
        if await self.findOne(data): 
            return None
        await self.collection.insert_one({
            "content" : data
        })
        return {
            "content" : data
        }
    
    async def delete(self,data):
        return await self.collection.delete_one({
            "content" : data
        })
        

class LobbyDropDown(discord.ui.Select):
    def __init__(self,server_lobbies,author, on_item_added):
        self.server_lobbies = server_lobbies
        self.author = author
        self.on_item_added = on_item_added
        
        options = [discord.SelectOption(label=lobby["lobbyname"], value=lobby["lobbyname"]) for lobby in self.server_lobbies]
        super().__init__(
            placeholder="Select a lobby",
            options=options,
            min_values=1,
            max_values=1
        )
    async def callback(self, interaction):
        if interaction.user == self.author:
            await interaction.response.defer()
            await self.on_item_added(interaction.data['values'][0])
                 
class ConnectDropDown(discord.ui.View):
    def __init__(self, author, server_lobbies):
        super().__init__()
        self.lobby = None
        self.add_item(LobbyDropDown(server_lobbies,author, self.on_item_added))

    async def on_item_added(self,value):
        self.lobby = value
        self.stop()
class Choice(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.value = None

    @discord.ui.button(label="Yes" , style=discord.ButtonStyle.green)
    async def btn1(self, interaction: discord.interactions, btn:discord.ui.button):
        if interaction.user == self.author:
            self.value = True
            await interaction.response.defer()
            self.stop()

    @discord.ui.button(label="Back" , style=discord.ButtonStyle.red)
    async def btn2(self, interaction: discord.interactions, btn:discord.ui.button):
        if interaction.user == self.author:
            self.value = False
            await interaction.response.defer()
            self.stop()

class LobbyRepository():
    def __init__(self,db):
        self.collection = db.lobby_collection()

    async def findAll(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)
    
    async def findOne(self,lobbyname):
        return await self.collection.find_one({"lobbyname":lobbyname})
    
    async def create(self, data):
        if await self.findOne(data["lobbyname"]): 
            return None
        await self.collection.insert_one({
            "lobbyname": data["lobbyname"],
            "description": data["description"],
            "limit":data["limit"]
        })
        return {
            "lobbyname": data["lobbyname"],
            "description": data["description"],
            "limit":data["limit"]
        }
    
    async def delete(self,data):
        if await self.findOne(data["lobbyname"]): 
            return await self.collection.delete_one({
                "lobbyname": data["lobbyname"],
            })
        else:
            return None
        
    
    async def lobbylimit(self):
        response  = await self.findAll()
        if response:
            hashmap = {}
            for data in response:
                hashmap[data["lobbyname"]] = int(data["limit"])

            return hashmap
        

    async def getAllLobbies(self):
        response  = await self.findAll()
        if response:
            list = []
            for data in response:
                list.append(data)

            return list
        

class GuildRepository():
    def __init__(self, db):
        self.collection = db.guilds_collection()

    async def findFilter(self, filter):
        cursor = self.collection.find(filter)
        return await cursor.to_list(length=None)
    
    async def findAll(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)
    
    async def findOne(self, server_id):
        return await self.collection.find_one({"server_id": server_id})

    async def create(self, data):
        if await self.findOne(data["server_id"]):  
            return None
        try:
            await self.collection.insert_one({
                "server_id": data["server_id"],
                "server_name": data["server_name"],
                "channels": data["channels"]
            }) 
            return True 
        except:
            return False

    async def delete(self,data):
        if await self.findOne(data["server_id"]):  
            await self.collection.delete_one({"server_id": data["server_id"]})  # Delete the guild document
            return True
        else:
            return False  
        
    async def update(self,data):
        if await self.findOne(data["server_id"]):  
            result = await self.collection.update_one(
                {"server_id": data["server_id"]},
                {"$set": {"channels": data["channels"]}}
            ) 
            return result.modified_count > 0
        else:
            return None  
