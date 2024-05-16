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

class OpenWorldServer(commands.Cog):
  def __init__(self, bot:commands.Bot):
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
    
  def get_lobby_limit(self, lobby_name: str) -> Optional[int]:
        return self.lobby_limits.get(lobby_name)

  async def is_lobby_full(self, lobby_name: str, lobby_limit: int) -> bool:
      lobby_users = await self.get_lobby_users(lobby_name)
      return len(lobby_users) >= lobby_limit

  async def create_guild_document(self, guild_id: int, channel_id: int, server_name: str, lobby_name: str):
      guild_document = await self.bot.db.guilds_collection.find_one({"server_id": guild_id})
      if guild_document:
          channels = guild_document.get("channels", [])
          if any(channel.get("channel_id") == channel_id for channel in channels):
              return False  # Channel already exists in guild document
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
      guild_document = await self.bot.db.guilds_collection.find_one({"server_id": guild_id})
      if guild_document:
          channels = guild_document.get("channels", [])
          for channel in channels:
              if channel["channel_id"] == channel_id:
                  channel["lobby_name"] = lobby_name
                  break
          await self.bot.db.guilds_collection.update_one({"server_id": guild_id}, {"$set": {"channels": channels}})

  async def delete_guild_document(self, guild_id: int, channel_id: int):
      guild_document = await self.bot.db.guilds_collection.find_one({"server_id": guild_id})
      if guild_document:
          channels = guild_document.get("channels", [])
          channels = [channel for channel in channels if channel["channel_id"] != channel_id]
          if channels:
              await self.bot.db.guilds_collection.update_one({"server_id": guild_id}, {"$set": {"channels": channels}})
          else:
              await self.bot.db.guilds_collection.delete_one({"server_id": guild_id})

  
  @commands.hybrid_command(name='connect', description='Link to Open World')
  @commands.has_permissions(kick_members=True)
  async def openworldlink(self, ctx, channel: discord.TextChannel):
      print("Open World Pass 1")
      guild_id = ctx.guild.id
      channel_id = channel.id

      print("Open World Pass 2")
      existing_guild = await self.find_guild(guild_id, channel_id)
      if existing_guild:
          await ctx.send(":no_entry: **Your channel is already registered for Open World Chat**\n\n**Type `a!unlink` to unlink your Open World**\n*This will only unlink from the Open World channel*")
          return

      sent_message = await ctx.send('Logging in...')
      await asyncio.sleep(1)
      await sent_message.edit(content='Linking into Open World Server...')
      await asyncio.sleep(1)
      await sent_message.edit(content=f'Confirming Connection with World - `{ctx.guild.id}`...')
      await asyncio.sleep(1)
      await sent_message.edit(content=f'Fetching Data from World - `{ctx.guild.id}`...')
      await asyncio.sleep(1)

      if not self.server_lobbies:
          await sent_message.edit(content=':no_entry: **All lobbies are currently full. Please contact the developer for assistance.**')
          return

      lobby_name = random.choice(self.server_lobbies)
      lobby_limit = self.get_lobby_limit(lobby_name)

      if lobby_limit is not None:
          lobby_count = await self.get_lobby_count(lobby_name)
          if lobby_count >= lobby_limit:
              await sent_message.edit(content=':no_entry: **All lobbies are currently full. Please contact the developer for assistance.**')
              return

      await sent_message.edit(content=f':white_check_mark: **LINK START!! You are now connected to {lobby_name}**')
      await asyncio.sleep(1)
      await self.create_guild_document(guild_id, channel_id, ctx.guild.name, lobby_name)

      message = await ctx.send("Thank you for linking with Open World Server!\nContact your Server Owners and ask them to contact the developer if any difficulties or suggestions!\nHave Fun chatting and maintain a friendly environment!\n\nIF YOU SEE ANY MESSAGE THAT BREAKS THE RULES, kindly report it by long-pressing the message > apps > report message by Ari Toram.\nThank you!")
      await message.add_reaction('✅')
  

  @commands.hybrid_command(name='switch', description='Switch to a different server lobby')
  @commands.has_permissions(kick_members=True)
  async def switch_lobby(self, ctx, *, new_lobby: str):
      guild_id = ctx.guild.id
      channel_id = ctx.channel.id

      existing_guild = await self.find_guild(guild_id, channel_id)
      if existing_guild:
          channels = existing_guild.get("channels", [])
          for channel in channels:
              if channel["channel_id"] == channel_id:
                  current_lobby = channel["lobby_name"]
                  if current_lobby == new_lobby:
                      await ctx.send(f":no_entry: **You are already in the {new_lobby} lobby**")
                      return

                  if new_lobby in self.server_lobbies:
                      lobby_limit = self.get_lobby_limit(new_lobby)
                      if lobby_limit is not None:
                          lobby_count = await self.get_lobby_count(new_lobby)
                          if lobby_count >= lobby_limit:
                              await ctx.send(":no_entry: **The lobby is currently full**")
                              return

                      channel["lobby_name"] = new_lobby
                      await self.update_guild_lobby(guild_id, channel_id, new_lobby)
                      await ctx.send(f":white_check_mark: **You have switched to {new_lobby}**")
                  else:
                      if new_lobby in self.private_lobbies and await self.is_private_lobby(new_lobby, ctx.author, ctx):
                          channel["lobby_name"] = new_lobby
                          await self.update_guild_lobby(guild_id, channel_id, new_lobby)
                          await ctx.send(f":white_check_mark: **You have switched to {new_lobby}**")
                      else:
                          await ctx.send(":no_entry: **That lobby is not available or the password is incorrect**")
                  return
      await ctx.send(":no_entry: **Your channel is not registered for Open World Chat**")

  
  
  async def get_lobby_count(self, lobby_name: str) -> int:
      count = 0
      async for document in self.bot.db.guilds_collection.find():
          channels = document.get("channels", [])
          for channel in channels:
              if channel.get("lobby_name") == lobby_name:
                  count += 1
      return count
  
  
  async def is_private_lobby(self, lobby_name: str, author: discord.Member, ctx) -> bool:
      private_lobbies = self.private_lobbies
  
      if lobby_name in private_lobbies:
          def check(m):
              return m.author == author and m.channel == ctx.channel
          
          await ctx.send(":lock: **Please enter the lobby password:**")
          
          try:
              password_response = await self.bot.wait_for('message', check=check, timeout=30.0)
          except asyncio.TimeoutError:
              return False
          
          entered_password = password_response.content.strip()
          correct_password = private_lobbies[lobby_name]
          
          if entered_password == correct_password:
              return True
      return False
      
  
  
    
  

  @commands.hybrid_command(name='unlink', description='Unlink from Open World')
  @commands.has_permissions(kick_members=True)
  async def openworldunlink(self, ctx):
      guild_id = ctx.guild.id
      channel_id = ctx.channel.id

      existing_guild = await self.find_guild(guild_id, channel_id)
      if existing_guild:
          await self.delete_guild_document(guild_id, channel_id)
          await ctx.send(":white_check_mark: **Unlinked from Open World Chat**")
      else:
          await ctx.send(":no_entry: **Your channel is not registered for Open World Chat**")

  async def find_guild(self, guild_id: int, channel_id: int):
      guild_document = await self.bot.db.guilds_collection.find_one({"server_id": guild_id})
      if guild_document:
          channels = guild_document.get("channels", [])
          for channel in channels:
              if channel["channel_id"] == channel_id:
                  return guild_document
      return None

  @commands.Cog.listener()
  async def on_message(self, message):
        print("On message Pass")
        muted_collection = self.bot.db.muted_collection
        guilds_collection = self.bot.db.guilds_collection
    
        if message.author.bot:
            return
    
        user_id = message.author.id
        muted_document = await muted_collection.find_one({"user_id": user_id})
    
        if muted_document:
            return
    
        await self.process_message(message, guilds_collection)
    
    
  async def process_message(self, message, guilds_collection):
      guild_id = message.guild.id
      channel_id = message.channel.id
      guild_document = await self.find_guild(guild_id, channel_id)
      if guild_document:
          channels = guild_document.get("channels", [])
          for channel in channels:
              if channel["channel_id"] == channel_id:
                  lobby_name = channel.get("lobby_name")
                  if lobby_name:
                      if lobby_name == "God Lobby":
                          await self.send_to_all_servers(message, lobby_name)
                      else:
                          await self.send_to_matching_lobbies(message, lobby_name, channel_id)
  
  
  async def send_to_all_servers(self, message, lobby_name):
      muted_collection = self.bot.db.muted_collection
      guilds_collection = self.bot.db.guilds_collection
  
      lobby_strengths = await self.get_lobby_strengths(guilds_collection)
      tasks = []
  
      async for document in guilds_collection.find():
          guild_id = document.get("server_id")
          channels = document.get("channels", [])
  
          for channel in channels:
              target_channel_id = channel.get("channel_id")
  
              if guild_id != message.guild.id and target_channel_id != message.channel.id:
                  guild = self.bot.get_guild(guild_id)
                  target_channel = guild.get_channel(target_channel_id)
  
                  if target_channel:
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
    muted_collection = self.bot.db.muted_collection
    guilds_collection = self.bot.db.guilds_collection

    lobby_strengths = await self.get_lobby_strengths(guilds_collection)
    tasks = []

    async for document in guilds_collection.find():
        guild_id = document.get("server_id")
        channels = document.get("channels", [])

        for channel in channels:
            target_channel_id = channel.get("channel_id")
            target_lobby_name = channel.get("lobby_name")

            if target_channel_id != channel_id and target_lobby_name == lobby_name:
                guild = self.bot.get_guild(guild_id)
                target_channel = guild.get_channel(target_channel_id)

                if target_channel:
                    strength = lobby_strengths.get(lobby_name, 0)
                    if "private" in lobby_name:
                        emoji = "🔒"  # Lock emoji for private lobbies
                    else:
                        emoji = "🌍"  # Earth emoji for public lobbies

                    content = f"{emoji} `{lobby_name}`\n:feather: **{message.guild.name} ☆ {message.author}  :\n\n**"
                    content += self.censor_bad_words(f"{message.content}\n\u200b", lobby_name)
                    
                    mentions = self.get_allowed_mentions(message, include_author=False)
                    task = asyncio.create_task(target_channel.send(content, allowed_mentions=mentions))

                    for attachment in message.attachments:
                        attachment_task = asyncio.create_task(target_channel.send(content=attachment.url))
                        tasks.append(attachment_task)

                    tasks.append(task)

    await asyncio.gather(*tasks)
  
  
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
  
  
  def censor_bad_words(self, content, lobby_name):
      if lobby_name == "God Lobby":
          return content
  
    #   with open("./BadWords.txt", "r") as file:
    #       bad_words = [line.strip() for line in file.readlines()]
  
    #   censored_content = content
    #   for word in bad_words:
    #       pattern = r"\b" + re.escape(word) + r"\b"
    #       censored_word = word[0] + "*" * (len(word) - 1)
    #       censored_content = re.sub(pattern, censored_word, censored_content, flags=re.IGNORECASE)
      return content
  
  
  def get_allowed_mentions(self, message, include_author=True):
      allowed_mentions = discord.AllowedMentions.none()
  
      return allowed_mentions
  
  

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
    print("Global Chat Cog loaded")
    await bot.add_cog(OpenWorldServer(bot))