
import logging
import discord

import asyncio

import re

import aiohttp
from discord.ext import commands
from discord import Embed
from discord_webhook import DiscordEmbed, DiscordWebhook


log = logging.getLogger("openworld.cog")

class OpenWorldServer(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.server_lobbies = None
        self.repositoryInitialize()
    # Caching data
    async def cog_load(self):
        self.server_lobbies = await self.lobby_repository.findAll()
        log.info("Servers: " + str(self.server_lobbies))

        self.muted_users = await self.muted_repository.findAll()
        log.info("muted_users: " + str(self.muted_users))

        self.malicious_urls = await self.malicious_urls.findAll()
        log.info("malicious_urls: " + str(self.malicious_urls))

        self.malicious_words = await self.malicious_words.findAll()
        log.info("malicious_words: " + str(self.malicious_words))

    @commands.command(name="reloaddata")
    async def reload(self,ctx):
        self.gc_cog = self.bot.get_cog("GlobalChatMod")
        await self.cog_load()
        await self.gc_cog.cog_load()
        await ctx.send(embed=Embed(
            description=" Data Loaded ",
        ))

    
    def repositoryInitialize(self):
        log.info(self.bot.db)
        self.muted_repository = MutedRepository(self.bot.db)
        self.lobby_repository = LobbyRepository(self.bot.db)
        self.malicious_urls = MaliciousURLRepository(self.bot.db)
        self.malicious_words = MaliciousWordsRepository(self.bot.db)

    @commands.command(name="reloaddata")
    async def reload(self,ctx):
        self.gc_cog = self.bot.get_cog("GlobalChatMod")
        await self.cog_load()
        await self.gc_cog.cog_load()
        await ctx.send(embed=Embed(
            description=" Data Loaded ",
        ))

    
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
            
    async def create_guild_document(self, guild_id, channel : discord.TextChannel, server_name, lobby_name):

        channel_id = channel.id

        guild_document = await self.bot.db.guilds_collection.find_one({"server_id": guild_id})
        webhook = await channel.create_webhook(name=server_name)
        if guild_document:

            channels = guild_document.get("channels", [])
            
            if any(channel.get("channel_id") == channel_id for channel in channels):
                return False 

            channels.append({"channel_id": channel_id, "lobby_name": lobby_name, "webhook": webhook.url})
            
          
            await self.bot.db.guilds_collection.update_one({"server_id": guild_id}, {"$set": {"channels": channels}})
        else:

            await self.bot.db.guilds_collection.insert_one({
                "server_id": guild_id,
                "channels": [{"channel_id": channel_id, "lobby_name": lobby_name, "webhook": webhook.url}],
                "server_name": server_name,

            })
        return True

    async def update_guild_lobby(self, guild_id: int, channel_id: int, lobby_name: str):
        # Gets the guild data
        guild_document = await self.bot.db.guilds_collection.find_one({"server_id": guild_id})
        # if data exists
        if guild_document:
            # Get all channels within the guild
            channels = guild_document.get("channels", [])
            # Iterate for each channel in channels
            for channel in channels:
                # If channel["channel_id"] matches the given channel id
                # then we update the channel["lobby_name"] to its lobby name then break
                if channel["channel_id"] == channel_id:
                    channel["lobby_name"] = lobby_name
                    break
            # then update the data in the database
            await self.bot.db.guilds_collection.update_one({"server_id": guild_id}, {"$set": {"channels": channels}})
            
    async def delete_guild_document(self, guild_id: int, channel_id: int):
        # Gets the guild data
        guild_document = await self.bot.db.guilds_collection.find_one({"server_id": guild_id})

        # If data exists
        if guild_document:
            # Get all channels within the guild
            channels = guild_document.get("channels", [])

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
                    await self.bot.db.guilds_collection.update_one(
                        {"server_id": guild_id}, {"$set": {"channels": channels}}
                    )
                else:
                    # Otherwise, delete the guild document
                    await self.bot.db.guilds_collection.delete_one({"server_id": guild_id})

    @commands.hybrid_command(name='testhook', description='Webhook test')
    async def testWebhook(self, ctx):
        try:
            user_name = ctx.author.display_name
            
            async with aiohttp.ClientSession() as session:
                async with session.get(ctx.author.avatar.url) as resp:
                    avatar_bytes = await resp.read()

            # Create the webhook
            webhook = await ctx.channel.create_webhook(name=user_name, avatar=avatar_bytes)

            # Create a DiscordWebhook object with the webhook URL
            webhook_url = webhook.url
            webhook_obj = DiscordWebhook(url=webhook_url)

            # Create an embed
            embed = DiscordEmbed(title="Your Title", description="Lorem ipsum dolor sit", color=0x03b2f8)
            embed.set_timestamp()

            # Add the embed to the webhook
            webhook_obj.add_embed(embed)

            # Send the webhook
            # response = "Webhook has been created for this guild"
            response = webhook_obj.execute()

            # Respond to the user
            await ctx.send(response)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
    
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
            existing_guild = await self.find_guild(guild_id, channel_id)
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
                
                # This is a duplicate from current_lobby command
                guilds = await self.getAllGuildUnderLobby(about)
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
                    description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
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
        
        async def CheckLobby(sent_message):
            # Lobby checker

            # # what is this code block??
            # if not self.server_lobbies:
            #     await sent_message.edit(content=':no_entry: **All lobbies are currently full. Please contact the developer for assistance.**')
            #     return

            # # Select by random a lobby name
            # lobby_name = random.choice(self.server_lobbies)
            # lobby_limit = self.get_lobby_limit(lobby_name)
            
            # # this part confuses me by the statement of not None 
            # if lobby_limit is not None:
            #     lobby_count = await self.get_lobby_count(lobby_name)
            #     if lobby_count >= lobby_limit:
            #         await sent_message.edit(content=':no_entry: **All lobbies are currently full. Please contact the developer for assistance.**')
            #         return
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
                description="<Insert Message>",
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
            
            response = isFailed(await Validation(guild_id, channel_id))
   
            responseWithlobby = isFailed(await SelectLobbies(guild_id, response['message_data']))

            response = isFailed(await Login(guild_id, responseWithlobby['message_data']))

            response = isFailed(await CheckLobby(response['message_data']))
            
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
        existing_guild = await self.find_guild(guild_id, channel_id)
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

    # This is a function mainly finding the guild document if it exist in the database
    async def find_guild(self, guild_id: int, channel_id: int):
        # Queries from the database
        guild_document = await self.bot.db.guilds_collection.find_one({"server_id": guild_id})

        # if it exist
        if guild_document:
            # get all the channels
            channels = guild_document.get("channels", [])
            # this code block check if it matches channel= channel_id
            for channel in channels:
                if channel["channel_id"] == channel_id:
                    return guild_document
        # else it returns Non
        return None

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
    async def on_message(self, message: discord.Message):

        if message.content.startswith("a!") or message.author.bot:
            return

        guild_id = message.guild.id
        channel_id = message.channel.id
        user_id = message.author.id
        sender = self.bot.get_user(user_id)
        guild_document = await self.find_guild(guild_id, channel_id)
        
        muted = self.isUserBlackListed(user_id)

        
        if not guild_document:
            return
        
        if muted:
            await message.delete()
            await sender.send(embed=Embed(description=f"You have been muted for {muted["reason"]}"))
            return
        
        if self.contains_malicious_url(message.content):
            await message.delete()
            await message.author.send(embed = Embed( description= "Your message contains malicious content. Please refrain from using inappropriate language or sharing harmful links."))    
            await self.log_report(message, "Sending Malicious Content")
            return
        # Calls for process_message method
        await self.process_message(message,guild_document, channel_id)

    
    async def process_message(self, message: discord.Message, guild_document, channel_id):
        # This function determines if where lobby should the message be sent 
        channels = guild_document.get("channels", [])        
        for channel in channels:
            if channel["channel_id"] == channel_id and channel["webhook"]:    
                await self.send_to_matching_lobbies(message, channel['lobby_name'], channel_id)
            elif not channel["webhook"]:
                await message.channel.send("Re-register this channel for webhook registration")

    async def send_to_matching_lobbies(self, message: discord.Message, lobby_name, channel_id):

        guilds_collection = self.bot.db.guilds_collection

        # message_queue = asyncio.Queue()
        async for document in guilds_collection.find():


                guild_id = document.get("server_id")
                channels = document.get("channels", [])

                for channel in channels:
                    target_channel_id = channel.get("channel_id")
                    target_lobby_name = channel.get("lobby_name")
                    # Checks if its not the guild and the channels via id basically filtered out the current channel
                    if target_channel_id != channel_id and target_lobby_name == lobby_name:
                        
                        webhook_url = channel.get("webhook")

                        # gets the guild information and the channel information
                        if webhook_url:
                            
                            

                            allowed_mentions = {
                                "parse" : ["users"]
                            }
                            webhook_obj = DiscordWebhook(
                                url=webhook_url,
                                avatar_url = message.author.avatar.url,
                                username =f"{message.author.display_name } || {message.guild.name}",
                                content= message.content,
                                allowed_mentions = allowed_mentions
                                )
                            
                            if(message.type == discord.MessageType.reply):
                                if message.reference:
                                    replied_message = await message.channel.fetch_message(message.reference.message_id)

                                    embed = DiscordEmbed(
                                        title=f"Reply from {message.author.display_name}",
                                        description=f"<@{replied_message.author.id}> Replying to your message: {replied_message.content}",
                                        color='03b2f8'  # Blue color (use hex code)
                                    )
                                    webhook_obj.add_embed(embed)

                            # Append attachments to the content if there are any
                            files = []
                            for attachment in message.attachments:
                                file = await attachment.to_file()
                                webhook_obj.add_file(file=file.fp, filename= file.filename)

                            webhook_obj.execute()

        # while not message_queue.empty():
        #     target_channel, content, mentions, attachments = await message_queue.get()
        #     await target_channel.send(content, allowed_mentions=mentions)
        #     for attachment in attachments:
        #         attachment_task = asyncio.create_task(target_channel.send(content=attachment.url))
        #         await attachment_task
        
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

        guild_document = await self.find_guild(guild_id,channel_id)

        if self.server_lobbies:
            if guild_document:

                lobby = guild_document.get("channels",[])
            
                for channel in lobby:
                    if channel["channel_id"] == channel_id:
                        lobby_name = channel['lobby_name']
                        limit = self.get_limit_server_lobby(lobby_name)
                        guilds = await self.getAllGuildUnderLobby(channel['lobby_name'])
                        connection = await self.get_lobby_count(channel['lobby_name'])

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
                            description= "Some description",
                            color= 0xFFC0CB 
                        )
                        embed.add_field(name="Guild Connected to the lobby", value = data)
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

            existing_guild = await self.find_guild(guild_id, channel_id)

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


    async def log_report(self,message,reason):
        guild = self.bot.get_guild(939025934483357766)
        target_channel = guild.get_channel(1230069779071762473)

        embed = Embed(
            title="Detected by system",
            description= f"**User {message.author.name} has been flagged due {reason}**\n\n**Message:**\n\n {message.content}"
        )
        embed.set_footer(text = f"userid {message.author.id}")
        await target_channel.send(embed=embed)

    #   async def is_private_lobby(self, lobby_name: str, author: discord.Member, ctx) -> bool:
    #       private_lobbies = self.private_lobbies
    
    #       if lobby_name in private_lobbies:
    #           def check(m):
    #               return m.author == author and m.channel == ctx.channel
            
    #           await ctx.send(":lock: **Please enter the lobby password:**")
            
    #           try:
    #               password_response = await self.bot.wait_for('message', check=check, timeout=30.0)
    #           except asyncio.TimeoutError:
    #               return False
            
    #           entered_password = password_response.content.strip()
    #           correct_password = private_lobbies[lobby_name]
            
    #           if entered_password == correct_password:
    #               return True
    #       return False
        

    def get_allowed_mentions(self, message, include_author=True):
        allowed_mentions = discord.AllowedMentions.none()

        return allowed_mentions   
    
    async def getAllLobby(self, current_guild=None):
        lobby_data = {lobby["lobbyname"]: 0 for lobby in self.server_lobbies}
        
        if current_guild is not None:
            filter_query = {"_id": {"$ne": current_guild}}
        else:
            filter_query = {}  # Empty filter if current_guild is None
        
        async for document in self.bot.db.guilds_collection.find(filter_query):
            channels = document.get("channels", [])
            
            for channel in channels:
                lobby_name = channel['lobby_name']
                
                if lobby_name in lobby_data:  # Check if the lobby is in the lobby_data dictionary

                    lobby_data[lobby_name] += 1  # Increment count for the lobby

        formatted_data = [{"name": lobby, "connection": count} for lobby, count in lobby_data.items()]
        
        return formatted_data
    
    async def getLobbyConnections(self,lobby_name,current_guild=None):
        if current_guild is not None:
            filter_query = {"_id": {"$ne": current_guild}, "channels.lobby_name": lobby_name}
        else:
            filter_query = {"channels.lobby_name": lobby_name}  # Filter by lobby_name if current_guild is None
        lobby_connection_count = 0
        async for document in self.bot.db.guilds_collection.find(filter_query):
            channels = document.get("channels", [])
            
            for channel in channels:
                if channel['lobby_name'] == lobby_name:
                    lobby_connection_count += 1

        return {"name": lobby_name, "connection": lobby_connection_count}
    # Scuffed Code
    async def getAllGuildUnderLobby(self, lobby_name):
        guilds = []
        async for document in self.bot.db.guilds_collection.find():
            channels = document.get("channels",[])
            for channel in channels:
                if lobby_name == channel.get("lobby_name"):
                    guilds.append(document)
        return guilds


        
async def setup(bot:commands.Bot):
    await bot.add_cog(OpenWorldServer(bot))


class MaliciousURLRepository():
    def __init__(self, db):
        self.db = db
        self.collection = self.db.malurl_collection

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
    def __init__(self,bot):
        self.collection = bot.db.guilds_collection

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
        self.db = db
        self.collection = self.db.malword_collection

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
        self.db = db
        self.collection =  self.db.lobby_collection

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
        