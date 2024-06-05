
import asyncio
from enum import Enum
import logging
import re

from discord import Embed
import discord

from .global_chat_listeners import MessageTypes

log = logging.getLogger("globalchat.init")

class Intialization:
    def __init__(self,bot):
        self.bot = bot
        self.bypass_delete_listener = set()

        # TODO: Move this somewhere maybe as a json file
        self.openworldThanksMessage = ("Thanks for connecting to the Open World Server! \n\n"+
        "**Remember to:** \n" +
        "> Be respectful and considerate. \n" +
        "> Protect your privacy. \n" +
        "> Follow our community guidelines.\n" +
        "> No NSFW or Lewd content\n"+
        "> Keep the chats Family Friendly and Clean\n\n"
        "If you see anyone breaking the rules, use ` /report ` and our global mods will take care of it!\n\n"
        "- Once the message is sent, it cannot delete be deleted from other servers. Please be mindful of what you send")

    async def load_data(
            self,
            guild_repository,
            lobby_repository,
            muted_repository,
            malicious_urls_repository,
            malicious_words_repository,
            moderator_repository):
        
        self.guild_data  = await guild_repository.findAll()
        
        self.server_lobbies = await lobby_repository.findAll()

        self.muted_users = await muted_repository.findAll()

        self.malicious_urls = await malicious_urls_repository.findAll()

        self.malicious_words = await malicious_words_repository.findAll()

        self.moderator = await moderator_repository.findAll()


        # All Functions that needs this data / a helper functions will be put here
    # More Generalize functions that speicifcs such as validating users if its a mode
    
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
    
    
    # Currently used for reply 
    async def find_messageID(self, target_channel_id,combined_ids):
        channel = self.bot.get_channel(target_channel_id)

        fetch_tasks = [self.try_fetch_message(target_channel_id, data, channel) for data in combined_ids]
       
        fetched_messages = await asyncio.gather(*fetch_tasks)
        
        replied_message = next((msg for msg in fetched_messages if msg is not None), None)
        return replied_message
    
    async def try_fetch_message(self, target_channel_id, data, channel):
        try:
            if data["channel"] == target_channel_id:
                return await channel.fetch_message(data["messageId"])
        except discord.NotFound:
            return None


    def contains_malicious_url(self, content):
        if self.malicious_urls and self.malicious_words:
            for url in self.malicious_urls:
                if re.search(url['content'],content, re.IGNORECASE):
                    return True ,url['content']
                
            for word in self.malicious_words:
                if word['content'].lower() in content.lower():
                    return True, word['content']
            
        return False, None

    def isUserBlackListed(self,id):
        if self.muted_users:
            for user in self.muted_users:
                if user["id"] == id:
                    return user
        return None

    def get_limit_server_lobby(self, name):
        for lobby in self.server_lobbies:
            if lobby["lobbyname"] == name:
                return lobby["limit"]


    def get_allowed_mentions(self, message, include_author=True):
        allowed_mentions = discord.AllowedMentions.none()

        return allowed_mentions   
    
    # TODO: Reduce Database usage and use the memory data than database queries
    async def getAllLobby(self):
        lobby_data = {lobby["lobbyname"]: 0 for lobby in self.server_lobbies}
        
        for document in self.guild_data:
            channels = document["channels"]
            
            for channel in channels:
                lobby_name = channel['lobby_name']
                
                if lobby_name in lobby_data:  # Check if the lobby is in the lobby_data dictionary

                    lobby_data[lobby_name] += 1  # Increment count for the lobby

        formatted_data = [{"name": lobby, "connection": count} for lobby, count in lobby_data.items()]
        
        sorted_data = sorted(formatted_data, key=lambda x: x["connection"], reverse=True)
    
        return sorted_data

    # TODO: Reduce Database usage and use the memory data than database queries
    async def getLobbyConnections(self,lobby_name, current_guild=None):
        
        lobby_connection_count = 0
        for document in self.guild_data:
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
    
    
    def get_lobby_count(self, lobby_name: str) -> int:
        count = 0
        for document in self.guild_data:
            channels = document.get("channels", [])
            for channel in channels:
                if channel.get("lobby_name") == lobby_name:
                    count += 1
        return count
    

    # ======================================================================================
    #  Log Report functions
    # ======================================================================================

    async def log_report(self,message,reason):
        guild = self.bot.get_guild(939025934483357766)
        target_channel = guild.get_channel(1230069779071762473)

        embed = Embed(
            title="Detected by system",
            description= f"**User {message.author.name} has been flagged due {reason}**\n\n**Message:**\n\n {message.content}"
        )
        embed.set_footer(text = f"userid {message.author.id}")
        await target_channel.send(embed=embed)

    
    
    async def chat_log_report(
            self,message : discord.Message, 
            messageType, 
            lobbyName,
            channel_id,
            message2 : discord.Message = None):
        channel = await self.bot.fetch_channel(channel_id)
        guild = self.bot.get_guild(939025934483357766)
        target_channel = guild.get_channel(1245210465919827979)
        
            
        if messageType == MessageTypes.DELETE:
            embed = Embed(
                description="**Chat log**\n\n"
                f"**User**: {message.author.global_name}\n"
                "**Action**: Delete\n"
                f"**Lobby**: {lobbyName}\n"
                f"**Message**: {message.content}\n"
                )
            embed.set_footer(text = f"userid {message.author.id} || message ID {message.id}")
            await target_channel.send(embed=embed)
        elif messageType == MessageTypes.UPDATE:
            embed=Embed(
                description="**Chat log**\n\n"
                f"**User**: {message.author.global_name}\n"
                "**Action**: Edit\n"
                f"**Lobby**: {lobbyName}\n"
                f"**Before**: {message2.content}\n"
                f"**After**: {message.content}"
                )
            embed.set_footer(text = f"userid {message.author.id} || message ID {message2.id}")
            await target_channel.send(embed = embed)
    