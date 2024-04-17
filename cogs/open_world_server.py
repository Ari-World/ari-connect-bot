import json
import discord
import datetime
import asyncio
import time
import re
import random
import io
import aiohttp
from typing import List
from typing import Optional
from discord import AllowedMentions
from discord.ext import commands
from discord import Embed
from plugins.ui import Choice, ConnectDropDown

class OpenWorldServer(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.server_lobbies = None

    # Caching data
    async def cog_load(self):
        self.server_lobbies = await self.bot.lobby_repository.findAll()
        print(self.server_lobbies)
        self.muted_users = await self.bot.muted_repository.findAll()
        print(self.muted_users)
        self.malicious_urls = await self.bot.malicious_urls.findAll()
        print(self.malicious_urls)
        self.malicious_words = await self.bot.malicious_words.findAll()
        print(self.malicious_words)

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
            
    async def create_guild_document(self, guild_id, channel_id, server_name, lobby_name):
        guild_document = await self.bot.db.guilds_collection.find_one({"server_id": guild_id})

        if guild_document:

            channels = guild_document.get("channels", [])
            
            if any(channel.get("channel_id") == channel_id for channel in channels):
                return False 

            channels.append({"channel_id": channel_id, "lobby_name": lobby_name})
            
          
            await self.bot.db.guilds_collection.update_one({"server_id": guild_id}, {"$set": {"channels": channels}})
        else:

            await self.bot.db.guilds_collection.insert_one({
                "server_id": guild_id,
                "channels": [{"channel_id": channel_id, "lobby_name": lobby_name}],
                "server_name": server_name
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

        # if Data exists
        if guild_document:
            # Get all Channels within the guild
            channels = guild_document.get("channels", [])
            
            # Checks out list if the channel exists.
            channels = [channel for channel in channels if channel["channel_id"] != channel_id]
            
            # If true
            if channels:
                # Update the data
                await self.bot.db.guilds_collection.update_one({"server_id": guild_id}, {"$set": {"channels": channels}})
            else:
                # else delete.
                await self.bot.db.guilds_collection.delete_one({"server_id": guild_id})

    
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
            await self.create_guild_document(guild_id, channel_id, guild_name, lobby)
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
    async def on_message(self, message):
        
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

    
    async def process_message(self, message, guild_document, channel_id):
        # This function determines if where lobby should the message be sent 
        channels = guild_document.get("channels", [])        
        for channel in channels:
            if channel["channel_id"] == channel_id:    
                await self.send_to_matching_lobbies(message, channel['lobby_name'], channel_id)

    async def send_to_matching_lobbies(self, message, lobby_name, channel_id):

        guilds_collection = self.bot.db.guilds_collection

        message_queue = asyncio.Queue()
        async for document in guilds_collection.find():

            guild_id = document.get("server_id")
            channels = document.get("channels", [])

            for channel in channels:
                target_channel_id = channel.get("channel_id")
                target_lobby_name = channel.get("lobby_name")
                # Checks if its not the guild and the channels via id basically filtered out the current channel
                if target_channel_id != channel_id and target_lobby_name == lobby_name:
                    
                    # gets the guild information and the channel information
                    guild = self.bot.get_guild(guild_id)
                    target_channel = guild.get_channel(target_channel_id)
                    
                    # if there's a channel registered in the guild
                    if target_channel:
                        
                        if "private" in lobby_name:
                            emoji = "🔒"  # Lock emoji for private lobbies
                        else:
                            emoji = "🌍"  # Earth emoji for public lobbies

                        content = f"{emoji} **{message.guild.name}**  \n\t\t`{message.author}`: {message.content}\n "

                        mentions = self.get_allowed_mentions(message, include_author=False)
                        attachments = [attachment for attachment in message.attachments]
                        await message_queue.put((target_channel, content, mentions,attachments))

        while not message_queue.empty():
            target_channel, content, mentions, attachments = await message_queue.get()
            await target_channel.send(content, allowed_mentions=mentions)
            for attachment in attachments:
                attachment_task = asyncio.create_task(target_channel.send(content=attachment.url))
                await attachment_task
                
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
                message = await self.show_lobbies_embed(ctx,"Available Lobbies")
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

    

    # @guilds_command.error
    # async def guilds_command_error(self, ctx, error):
    #     if isinstance(error, commands.MissingRequiredArgument):
    #         await self.guilds_command(ctx)    
    
    # @commands.command(name='admin_connect', description='Admin command to connect a server and channel')
    # @commands.has_permissions(administrator=True)
    # async def admin_connect(self, ctx, server_id: int, channel_id: int, lobby_name: str):
    #   existing_guild = await self.bot.db.guilds_collection.find_one({"server_id": server_id})
    #   if existing_guild:
    #       channels = existing_guild.get("channels", [])
    #       if any(channel.get("channel_id") == channel_id for channel in channels):
    #           await ctx.send("This channel is already registered for Open World Chat.")
    #           return

    #   server = self.bot.get_guild(server_id)
    #   if not server:
    #       await ctx.send(":no_entry: Invalid server ID.")
    #       return

    #   server_name = server.name

    #   if lobby_name not in self.server_lobbies:
    #       await ctx.send(":no_entry: Lobby name Invalid or Private.")
    #       return

    #   success = await self.create_guild_document(server_id, channel_id, server_name, lobby_name)

    #   if success:
    #       await ctx.send(f":white_check_mark: Server with ID {server_id} and channel with ID {channel_id} have been successfully registered for Open World Chat.")
    #       await ctx.send(f":earth_asia: Selected lobby: {lobby_name}")
    #   else:
    #       await ctx.send(":no_entry: Failed to create guild document.")
    
async def setup(bot:commands.Bot):
    await bot.add_cog(OpenWorldServer(bot))