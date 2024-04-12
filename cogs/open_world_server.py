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
    def __init__(self, bot:commands.Bot, db):
        self.bot = bot
        self.per_page = 5
        self.server_lobbies = ["Toram Lobby 1", "Toram Lobby 2", "Cafe Lobby 1", "Cafe Lobby 2"]
        self.private_lobbies = {
        "private_exile_alliance_guilds": "DrAzyGD"
        }

        self.lobby_limits = {
                "Toram Lobby 1": 17,
                "Toram Lobby 2": 15,
                "Cafe Lobby 1": 15,
                "Cafe Lobby 2": 15
            }
        
    # This gets the lobby limit using the variable lobby limits and return specific lobbies
    def get_lobby_limit(self, lobby_name: str) -> Optional[int]:
        return self.lobby_limits.get(lobby_name)

    # This is a boolean that returns if lobby is full
    async def is_lobby_full(self, lobby_name: str, lobby_limit: int) -> bool:
        lobby_users = await self.get_lobby_users(lobby_name)
        return len(lobby_users) >= lobby_limit

    #Create a Lobby
    async def create_guild_document(self, guild_id: int, channel_id: int, server_name: str, lobby_name: str):
        print("Creating Data")
        # Gets the database data in thte guilds_collection
        guild_document = await self.bot.db.guilds_collection.find_one({"server_id": guild_id})
        
        # Checks if the data exists
        if guild_document:
            print("Data exists, now finding if current channel exists")
            # If it exists it gets all channels
            channels = guild_document.get("channels", [])
            
            # Check if channels if the current channel is registerd in the collection channel under guild
            if any(channel.get("channel_id") == channel_id for channel in channels):
                print("Channel has been already registered")
                return False  # Channel already exists in guild document
            
            # if it doesn't, we append the channel ID to its exsisting guild
            #
            print("No data found")
            print("Creating data for the channel " + channel_id + " under lobby name " +lobby_name)
            channels.append({"channel_id": channel_id, "lobby_name": lobby_name})
            
            # Then we update the data with the new channel
            await self.bot.db.guilds_collection.update_one({"server_id": guild_id}, {"$set": {"channels": channels}})
        else:
            # if it doesnt exists in the data base, we create a new guild collection with its new data
            # Generate a data
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
            # Guild Validation process
            print("Openworld link module entered")
            embed = Embed(
                description="Preparing ...",
                color=0x7289DA 
            )
            sent_message = await ctx.send(embed=embed)
            print("Initialize data needed")
            # Initialize needed data
            
            

            print("Checking if channel exists")
            # Checks if the channel exists
            existing_guild = await self.find_guild(guild_id, channel_id)
            print(existing_guild)
            if existing_guild:
                embed = Embed(
                    title=":no_entry: Your channel is already registered for Open World Chat",
                    description="Type `a!unlink` to unlink your Open World\n*This will only unlink from the Open World channel*",
                    color=0xFF0000  # Red color
                )
                await sent_message.edit(embed=embed)
                return {'message':'Failed', 'message_data':sent_message}
            else:
                return {'message':'Success', 'message_data':sent_message}
        
        async def SelectLobbies(guild_id,sent_message):
            # Getting lobbies and selecting available lobbies
            # ======================================================================================
            # Issue: handle the issue of user selecting the full lobbies
            # ======================================================================================
            async def SelectLobby():
                lobby_data = await self.getAllLobby(guild_id)
                formatted_data = "**Available Lobby**\n"
                
                for data in lobby_data:
                    limit = self.lobby_limits[data['name']]
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
                    title="Select a lobby",
                    description= formatted_data,
                    color=0x7289DA 
                )
                await sent_message.edit(embed=embed)

                dropdown =ConnectDropDown()
                
                message = await ctx.send(view=dropdown)
                try:
                    await asyncio.wait_for(dropdown.wait(), timeout=60)
                except asyncio.TimeoutError:
                    await ctx.send("You didn't respond within the specified time.")
                    raise Exception("")
                
                await message.delete()
                return dropdown.lobby

            async def AboutLobby(about):

                guilds = await self.getAllGuildUnderLobby(about)
                print(guilds)
                data = ""
                x = 1
                if guilds:
                    for guild in guilds:
                        text = f"**{x}**) **{guild['server_name']}**"
                        data += text + "\n\n"
                        x += 1
                else:
                    data = "There's no guild connected to this lobby"
                choice = Choice()
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
            choice = False
            while not choice:
                about = await SelectLobby()
                choice = await AboutLobby(about)
                
                if choice is True:
                    return {'message':'Success', 'message_data':sent_message, 'lobby': about} 
        
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
        
        async def CreateConnection(dropdown,sent_message):
            # Create Connection
            # now connect
            embed = Embed(
                description=f':white_check_mark: **LINK START!! You are now connected to {dropdown}**',
                color=0x7289DA 
            )
            await sent_message.edit(embed=embed)
            await asyncio.sleep(1)
            # await self.create_guild_document(guild_id, channel_id, ctx.guild.name, lobby_name)
            
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
            
        async def Sequence(guild_id,channel_id):
            response = isFailed(await Validation(guild_id, channel_id))
            responseWithDropDown = isFailed(await SelectLobbies(guild_id, response['message_data']))
            response = isFailed(await Login(guild_id, responseWithDropDown['message_data']))
            response = isFailed(await CheckLobby(response['message_data']))
            response = isFailed(await CreateConnection(responseWithDropDown['lobby'], response['message_data']))
        # ======================================================================================
        # Runtime Manager
        guild_id = ctx.guild.id
        channel_id = channel.id

        # Sequence 
        await Sequence(guild_id,channel_id)
    
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
            await ctx.send(":white_check_mark: **Unlinked from Open World Chat**")
        else:
            # else if doesnt 
            await ctx.send(":no_entry: **Your channel is not registered for Open World Chat**")

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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            # Return if the sender is a bot
            return

        guild_id = message.guild.id
        channel_id = message.channel.id

        muted_collection = self.bot.db.muted_collection
        guilds_collection = self.bot.db.guilds_collection

        guild_document = await self.find_guild(guild_id, channel_id)
        if not guild_document:

            return

        # there might be a better optimization here
        user_id = message.author.id
        muted_document =  await muted_collection.find_one({"server_id": user_id})

        if muted_document:
            # Return if the sender is muted
            return
    
        # Calls for process_message method
        await self.process_message(message,guild_document, guild_id, channel_id)
    
    
    async def process_message(self, message, guild_document, guild_id, channel_id):
       
       
        channels = guild_document.get("channels", [])
        
        for channel in channels:
            # if channel id matches
            if channel["channel_id"] == channel_id:
                
                lobby_name = channel.get("lobby_name")
                # if lobby name exists
                if lobby_name:
                    if lobby_name == "God Lobby":
                        await self.send_to_all_servers(message, lobby_name)
                    else:
                        await self.send_to_matching_lobbies(message, lobby_name, channel_id)

    # This is set up for announcement messages
    async def send_to_all_servers(self, message, lobby_name):
        print("Sending message using the god lobby")
        # Initialize the variable needed
        muted_collection = self.bot.db.muted_collection
        guilds_collection = self.bot.db.guilds_collection

        # Get the lobby strength
        lobby_strengths = await self.get_lobby_strengths(guilds_collection)
        tasks = []
        
        # Loops for each document under guild_collection table
        async for document in guilds_collection.find():
            
           # Initialize the variable needed
            guild_id = document.get("server_id")
            channels = document.get("channels", [])
            # loops for each channels
            for channel in channels:
                # set up the targetted id
                target_channel_id = channel.get("channel_id")

                # Checks if its not the guild and the channels via id basically filtered out the current channel
                if guild_id != message.guild.id and target_channel_id != message.channel.id:
                    # gets the guild information and the channel information
                    guild = self.bot.get_guild(guild_id)
                    target_channel = guild.get_channel(target_channel_id)
                    
                    # if there's a channel registered in the guild
                    if target_channel:
                        # Message datas
                        strength = lobby_strengths.get(lobby_name, 0)
                        content = f"```diff\n- DEVs & MODs -\n{message.content}\n\n```"
                        mentions = self.get_allowed_mentions(message, include_author=False)
                        censored_content = self.censor_bad_words(content, lobby_name)
                        task = asyncio.create_task(target_channel.send(censored_content, allowed_mentions=mentions))

                        for attachment in message.attachments:
                            await task  # Wait for the message to be sent before sending the attachment
                            await target_channel.send(content=attachment.url)

                        tasks.append(task)

        await asyncio.gather(*tasks)
     
    async def send_to_matching_lobbies(self, message, lobby_name, channel_id):
        
        # Initialize the variable needed
        guilds_collection = self.bot.db.guilds_collection

        # Get the lobby strength
        lobby_strengths = await self.get_lobby_strengths(guilds_collection)
        tasks = []

        
        # Loops for each document under guild_collection table
        async for document in guilds_collection.find():

             # Initialize the variable needed
            guild_id = document.get("server_id")
            channels = document.get("channels", [])

            # loops for each channels
            
            for channel in channels:
                target_channel_id = channel.get("channel_id")
                target_lobby_name = channel.get("lobby_name")
                # Checks if its not the guild and the channels via id basically filtered out the current channel
                if target_channel_id != channel_id:
                    
                    # gets the guild information and the channel information
                    guild = self.bot.get_guild(guild_id)
                    target_channel = guild.get_channel(target_channel_id)

                    # if there's a channel registered in the guild
                    if target_channel:
                        strength = lobby_strengths.get(lobby_name, 0)
                        if "private" in lobby_name:
                            emoji = "🔒"  # Lock emoji for private lobbies
                        else:
                            emoji = "🌍"  # Earth emoji for public lobbies

                        # content = f"{emoji} `{lobby_name}`\n:feather: **{message.guild.name} ☆ {message.author}  :\n\n** {message.content}"
                        # content += self.censor_bad_words(f"{message.content}\n\u200b", lobby_name)
                        
                        content = f"{emoji} **{message.guild.name}** ` {message.author} `: {message.content}"

                        mentions = self.get_allowed_mentions(message, include_author=False)
                        task = asyncio.create_task(target_channel.send(content, allowed_mentions=mentions))

                        for attachment in message.attachments:
                            attachment_task = asyncio.create_task(target_channel.send(content=attachment.url))
                            tasks.append(attachment_task)

                        tasks.append(task)


        await asyncio.gather(*tasks)
    
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
    async def current_lobby(self,ctx):
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        print(channel_id)
        print(guild_id)
        guild_document = await self.find_guild(guild_id,channel_id)
        print(guild_document)
        if guild_document:

            lobby = guild_document.get("channels",[])
            print(lobby)
            for channel in lobby:
                if channel["channel_id"] == channel_id:
                    limit = self.lobby_limits[channel['lobby_name']]
                    connection = await self.get_lobby_count(channel['lobby_name'])

                    embed = Embed(
                        title= f"{channel['lobby_name']} - {connection}/{limit}",
                        color= 0xFFC0CB 
                    )
                    embed.add_field(name="Guild Connected to the lobby", value ="Currently Under development")
                    await ctx.send(embed=embed)
        else:
            embed = Embed(
                description=f":no_entry: **Your channel is not registered for Open World Chat**",
                color=0xFFC0CB
            )
            
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='lobbies', description='Current Lobby description')
    async def show_lobbies(self, ctx):
        lobby_data = await self.getAllLobby()
        formatted_data = ""
        
        for data in lobby_data:
            limit = self.lobby_limits[data['name']]
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
            title="Show Lobbies",
            description= "Some description to add",
            color=0x7289DA 
        )
        embed.add_field(name="Public Lobbies",value=formatted_data)
        return await ctx.send(embed=embed)
    @commands.hybrid_command(name='switch', description='Switch to a different server lobby')
    @commands.has_permissions(kick_members=True)
    async def switch_lobby(self, ctx, new_lobby: str):

        async def Menu(guild_id,channel_id):
            async def SelectLobby():
                message = self.show_lobbies()
                dropdown =ConnectDropDown()
                
                message = await ctx.send(view=dropdown)
                try:
                    await asyncio.wait_for(dropdown.wait(), timeout=60)
                except asyncio.TimeoutError:
                    await ctx.send("You didn't respond within the specified time.")
                    raise Exception("")
                
                await message.delete()
                return dropdown.lobby
            # ======================================================================================
            # Menu Manager
            choice
            while True:
                
                choice = self.current_lobby()
                lobby = SelectLobby()

        async def Validation(guild_id,channel_id):
            print("Validating")
            existing_guild = await self.find_guild(guild_id, channel_id)
            embed = Embed(
                description="Switching Lobbies ...",
                color=0x7289DA,
            )
            message = await ctx.send(embed=embed)

            if existing_guild:

                channels = existing_guild.get("channels",[])
                for channel in channels:
                    # Checks if user is in the lobby
                    if channel['channel_id'] == channel_id and channel['lobby_name'] == new_lobby:
                        embed = Embed( 
                            description=f":no_entry:**You are already in the {new_lobby} lobby** ", 
                            color=0x7289DA 
                        )
                        await message.edit(embed=embed)

                        return {'message': 'Failed', 'message_data': message, "channel": None}
                    elif channel['channel_id'] == channel_id:
                        return {'message': 'Success', 'message_data': message, "channel": channel}
            else:
                embed = Embed( 
                    description=f":no_entry: **Your channel is not registered for Open World Chat**",
                    color=0x7289DA 
                )
                await message.edit(embed=embed)

                return {'message': 'Failed', 'message_data': message, "channel": None}
        # Might change this to a drop down function
        async def isLobbyFull( sent_message, channel):
            print("Checking if the lobby is full")
            if new_lobby in self.server_lobbies:
                print("pass 0")
                lobby_limit = self.get_lobby_limit(new_lobby)
                lobby_count = await self.get_lobby_count(new_lobby)
                print("Pass 1")
                if lobby_count == lobby_limit:
                    embed = Embed( 
                            description=f":no_entry: **The lobby is currently full**", 
                            color=0x7289DA 
                        )
                    print("Pass 2")
                    await sent_message.edit(embed=embed)
                    return {'message': 'Failed', 'message_data': sent_message, "channel": None}
                else:
                    return {'message': 'Success', 'message_data': sent_message, "channel": channel}
            else:
                print("pass")
                return {'message': 'Failed', 'message_data': sent_message, "channel": None}
        
        
        async def updateLobbyConnection(guild_id, channel_id, channel, message):
            print("Updating data")
            channel["lobby_name"] = new_lobby
            await self.update_guild_lobby(guild_id, channel_id,channel)
            embed = Embed(
                description=f":white_check_mark: **You have switched to {new_lobby}**",
                color=0x7289DA 
            )
            await message.edit(embed=embed)
        def isFailed(response):
            if(response['message'] == "Failed"):
                raise Exception("")
            else:
                return response
        async def Sequence(guild_id,channel_id):
            response = isFailed(await Menu(guild_id,channel_id))
            response = isFailed(await Validation(guild_id, channel_id))

            response = isFailed(await isLobbyFull( response['message_data'] , response['channel']))
            print(response)
            updateLobbyConnection(guild_id,channel_id,response["channel"])
        # ======================================================================================
        # Run Time Manager
        # ======================================================================================
        # Potential Issues:
        # - Chat still goes even during switching
        # - 
        # ======================================================================================
        
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id

        # Sequence
        await Sequence(guild_id,channel_id)

        
        
    
    

    
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
        
    
    async def get_lobby_strengths(self, guilds_collection):
        lobby_strengths = {}
        async for document in guilds_collection.find():
            channels = document.get("channels", [])
            for channel in channels:
                lobby_name = channel.get("lobby_name")
                if lobby_name:
                    if lobby_name not in lobby_strengths:
                        lobby_strengths[lobby_name] = 0
                    lobby_strengths[lobby_name] += 1
        return lobby_strengths
    
    def get_allowed_mentions(self, message, include_author=True):
        allowed_mentions = discord.AllowedMentions.none()

        return allowed_mentions   
    
    def censor_bad_words(self, content, lobby_name):
        # if lobby_name == "God Lobby":
        #     return content

        # with open("./BadWords.txt", "r") as file:
        #     bad_words = [line.strip() for line in file.readlines()]

        # censored_content = content
        # for word in bad_words:
        #     pattern = r"\b" + re.escape(word) + r"\b"
        #     censored_word = word[0] + "*" * (len(word) - 1)
        #     censored_content = re.sub(pattern, censored_word, censored_content, flags=re.IGNORECASE)
        # return censored_content
        pass
    
    async def getAllLobby(self, current_guild=None):
        lobby_data = {lobby: 0 for lobby in self.server_lobbies}

        async for document in self.bot.db.guilds_collection.find({"_id": {"$ne": current_guild}}):
            channels = document.get("channels", [])
            for channel in channels:
                lobby_name = channel.get("lobby_name")
                if lobby_name in lobby_data:  # Check if the lobby is in the lobby_data dictionary
                    lobby_data[lobby_name] += 1  # Increment count for the lobby

        formatted_data = [{"name": lobby, "connection": count} for lobby, count in lobby_data.items()]
        
        return formatted_data
    
    # Scuffed Code
    async def getAllGuildUnderLobby(self, lobby_name):
        guilds = []
        async for document in self.bot.db.guilds_collection.find():
            channels = document.get("channels",[])
            for channel in channels:
                if lobby_name == channel.get("lobby_name"):
                    guilds.append(document)
        return guilds

    # @commands.command(name='guilds')
    # async def guilds_command(self, ctx, selected_lobby=None):
    #   guilds_data = await self.bot.db.guilds_collection.find().to_list(length=None)
    #   guild_info = []

    #   for guild_data in guilds_data:
    #       server_name = guild_data["server_name"]
    #       channels = guild_data["channels"]
    #       lobby_names = []

    #       for channel in channels:
    #           lobby_name = channel["lobby_name"]

    #           if lobby_name in self.private_lobbies:
    #               lobby_name = ":lock: Private Lobby"  # Display as locked private lobby

    #           lobby_names.append(lobby_name)

    #       guild_info.append((server_name, lobby_names))

    #   if selected_lobby:
    #       filtered_guilds = [(server_name, lobby_names) for server_name, lobby_names in guild_info if selected_lobby in lobby_names]
    #   else:
    #       filtered_guilds = guild_info

    #   total_pages = (len(filtered_guilds) + self.per_page - 1) // self.per_page  # Calculate total pages
    #   page = 0  # Current page

    #   embed = discord.Embed(title=f"🌏 Information of {len(filtered_guilds)} Guilds Found", color=discord.Color.blue())
    #   message = None

    #   while True:
    #       embed.clear_fields()

    #       start_index = page * self.per_page
    #       end_index = min(start_index + self.per_page, len(filtered_guilds))

    #       for i, (server_name, lobby_names) in enumerate(filtered_guilds[start_index:end_index], start=start_index):
    #           value = "\n".join(lobby_names)
    #           embed.add_field(name=f"#{i+1} {server_name}", value=value, inline=False)

    #       embed.set_footer(text=f"Page {page + 1}/{total_pages}")

    #       if message:
    #           await message.edit(embed=embed)
    #       else:
    #           message = await ctx.send(embed=embed)

    #       previous_emoji = "⬅️"
    #       next_emoji = "➡️"
    #       close_emoji = "❌"

    #       await message.add_reaction(previous_emoji)
    #       await message.add_reaction(next_emoji)
    #       await message.add_reaction(close_emoji)

    #       def check(reaction, user):
    #           return user == ctx.author and str(reaction.emoji) in [previous_emoji, next_emoji, close_emoji]

    #       try:
    #           reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
    #           await message.clear_reactions()

    #           if str(reaction.emoji) == previous_emoji and page > 0:
    #               page -= 1
    #           elif str(reaction.emoji) == next_emoji and page < total_pages - 1:
    #               page += 1
    #           elif str(reaction.emoji) == close_emoji:
    #               await message.delete()
    #               break
    #       except asyncio.TimeoutError:
    #           break

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
    ari_instance = bot
    await bot.add_cog(OpenWorldServer(bot, ari_instance.db))