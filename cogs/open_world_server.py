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

from plugins.ui import ConnectDropDown

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
        print("Openworld link module entered")
        embed = Embed(
            description="Preparing ...",
            color=0x7289DA 
        )
        sent_message = await ctx.send(embed=embed)
        print("Initialize data needed")
        # Initialize needed data
        guild_id = ctx.guild.id
        channel_id = channel.id
        
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
            await ctx.send(embed=embed)
            return
        
        print("Preparing")

        embed = Embed(
            title="Select a lobby",
            description="Choose a lobby to join",
            color=0x7289DA 
        )
        await sent_message.edit(embed=embed)

        dropdown =ConnectDropDown()
        
        message = await ctx.send(view=dropdown)
        await dropdown.wait()
        
        await ctx.send(f"Selected: Lobby {dropdown.lobby}")
        await message.delete()
        embed = Embed(
            description="Logging in ...",
            color=0x7289DA 
        )
        await sent_message.edit(embed=embed)
        await asyncio.sleep(1)
        embed.description = "Linking into Open World Server..."
        await sent_message.edit(embed=embed)
        await asyncio.sleep(1)
        embed.description = f"Confirming Connection with World - `{ctx.guild.id}`..."
        await sent_message.edit(embed=embed)
        await asyncio.sleep(1)
        embed.description = f"Fetching Data from World - `{ctx.guild.id}`..."
        await sent_message.edit(embed=embed)
        await asyncio.sleep(1)

        # # what is this code block??
        # if not self.server_lobbies:
        #     await sent_message.edit(content=':no_entry: **All lobbies are currently full. Please contact the developer for assistance.**')
        #     return

        # # Select by random a lobby name
        lobby_name = random.choice(self.server_lobbies)
        # lobby_limit = self.get_lobby_limit(lobby_name)
        
        # # this part confuses me by the statement of not None 
        # if lobby_limit is not None:
        #     lobby_count = await self.get_lobby_count(lobby_name)
        #     if lobby_count >= lobby_limit:
        #         await sent_message.edit(content=':no_entry: **All lobbies are currently full. Please contact the developer for assistance.**')
        #         return


        # now connect
        embed.description = f':white_check_mark: **LINK START!! You are now connected to {lobby_name}**'
        await sent_message.edit(embed=embed)
        await asyncio.sleep(1)
        # await self.create_guild_document(guild_id, channel_id, ctx.guild.name, lobby_name)
        
        # sends a successful message
        embed = Embed(
            title="Thank you for linking with Open World Server!",
            description="Contact your Server Owners and ask them to contact the developer if any difficulties or suggestions!\nHave Fun chatting and maintain a friendly environment!\n\nIF YOU SEE ANY MESSAGE THAT BREAKS THE RULES, kindly report it by long-pressing the message > apps > report message by Ari Toram.\nThank you!",
            color=0x00FF00 
        )
        message = await ctx.send(embed=embed)
        await message.add_reaction('✅')
    
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
       
        print("Processing Message")
        print("Sender with ID: " + str(guild_id) + " and channel ID: " + str(channel_id))
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
        print("================== Sending message as matching lobbies")
        # Initialize the variable needed
        guilds_collection = self.bot.db.guilds_collection

        # Get the lobby strength
        lobby_strengths = await self.get_lobby_strengths(guilds_collection)
        tasks = []

        print("Fetching all guilds in the collection")
        
        # Loops for each document under guild_collection table
        async for document in guilds_collection.find():
            
            print("Preparing for data needing")
             # Initialize the variable needed
            guild_id = document.get("server_id")
            channels = document.get("channels", [])
            
            print("Sending messages to all registered channel")
            # loops for each channels
            
            for channel in channels:
                target_channel_id = channel.get("channel_id")
                target_lobby_name = channel.get("lobby_name")
                
                print(" target channel: " +  str(target_channel_id) +" current channel: " + str(channel_id))
                print(" target lobby name: " + str(target_lobby_name) + " current lobby name: " + str(lobby_name))
                # Checks if its not the guild and the channels via id basically filtered out the current channel
                if target_channel_id != channel_id:
                    print("Sending to channel "+ str(target_channel_id) + " |  Lobby: "+ str(target_lobby_name))
                    # gets the guild information and the channel information
                    guild = self.bot.get_guild(guild_id)
                    print(guild)
                    target_channel = guild.get_channel(target_channel_id)
                    print(target_channel)
                    # if there's a channel registered in the guild
                    if target_channel:
                        print("Preparing the message ")
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
                        print("Message Added to queue")

        await asyncio.gather(*tasks)
        print("All Message sent")
    
    async def get_lobby_count(self, lobby_name: str) -> int:
        count = 0
        async for document in self.bot.db.guilds_collection.find():
            channels = document.get("channels", [])
            for channel in channels:
                if channel.get("lobby_name") == lobby_name:
                    count += 1
        return count
    
    #   @commands.hybrid_command(name='switch', description='Switch to a different server lobby')
    #   @commands.has_permissions(kick_members=True)
    #   async def switch_lobby(self, ctx, *, new_lobby: str):
    #       guild_id = ctx.guild.id
    #       channel_id = ctx.channel.id

    #       existing_guild = await self.find_guild(guild_id, channel_id)
    #       if existing_guild:
    #           channels = existing_guild.get("channels", [])
    #           for channel in channels:
    #               if channel["channel_id"] == channel_id:
    #                   current_lobby = channel["lobby_name"]
    #                   if current_lobby == new_lobby:
    #                       await ctx.send(f":no_entry: **You are already in the {new_lobby} lobby**")
    #                       return

    #                   if new_lobby in self.server_lobbies:
    #                       lobby_limit = self.get_lobby_limit(new_lobby)
    #                       if lobby_limit is not None:
    #                           lobby_count = await self.get_lobby_count(new_lobby)
    #                           if lobby_count >= lobby_limit:
    #                               await ctx.send(":no_entry: **The lobby is currently full**")
    #                               return

    #                       channel["lobby_name"] = new_lobby
    #                       await self.update_guild_lobby(guild_id, channel_id, new_lobby)
    #                       await ctx.send(f":white_check_mark: **You have switched to {new_lobby}**")
    #                   else:
    #                       if new_lobby in self.private_lobbies and await self.is_private_lobby(new_lobby, ctx.author, ctx):
    #                           channel["lobby_name"] = new_lobby
    #                           await self.update_guild_lobby(guild_id, channel_id, new_lobby)
    #                           await ctx.send(f":white_check_mark: **You have switched to {new_lobby}**")
    #                       else:
    #                           await ctx.send(":no_entry: **That lobby is not available or the password is incorrect**")
    #                   return
    #       await ctx.send(":no_entry: **Your channel is not registered for Open World Chat**")

    
    

    
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
    

    # @commands.hybrid_command(name='lobbies', description='Show all lobby strength')
    # async def lobby_strength(self, ctx):
    #     guild_id = ctx.guild.id
    #     channel_id = ctx.channel.id

    #     existing_guild = await self.find_guild(guild_id, channel_id)
    #     current_lobby = ""
    #     if existing_guild:
    #         channels = existing_guild.get("channels", [])
    #         for channel in channels:
    #             if channel["channel_id"] == channel_id:
    #                 current_lobby = channel["lobby_name"]
    #                 break

    #     lobby_strengths = {lobby: {"count": 0, "limit": self.get_lobby_limit(lobby)} for lobby in self.server_lobbies}
    #     private_lobby_count = len(self.private_lobbies)
    #     private_lobby_members = 0  # Initialize the count of private lobby members

    #     async for document in self.bot.db.guilds_collection.find():
    #         channels = document.get("channels", [])
    #         for channel in channels:
    #             lobby_name = channel.get("lobby_name")
    #             if lobby_name in lobby_strengths:
    #                 lobby_strengths[lobby_name]["count"] += 1
    #             elif lobby_name in self.private_lobbies:  # Check if lobby is a private lobby
    #                 private_lobby_members += 1

    #     embed = discord.Embed(title="Lobby Strengths", color=discord.Color.green())

    #     for lobby in self.server_lobbies:
    #         count = lobby_strengths[lobby]["count"]
    #         limit = lobby_strengths[lobby]["limit"]
    #         emoji = ":red_circle:" if count >= limit else ":orange_circle:" if count >= limit/2 else ":green_circle:"
    #         lobby_display_name = lobby
    #         if lobby == current_lobby:
    #             lobby_display_name += " (Your Guild Lobby)"
    #         embed.add_field(name=f"{emoji} {lobby_display_name}", value=f"{count}/{limit} Guilds Connected", inline=False)

    #     private_lobby_display = f":lock: Private Lobbies: {private_lobby_count}\nMembers: {private_lobby_members}"
    #     embed.add_field(name="\u200b", value=private_lobby_display, inline=False)

    #     await ctx.send(embed=embed)
    
    
    
    
    
    
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