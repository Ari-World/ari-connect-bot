

# First time implementing this, 
# havent tried if I can have multiple event listner 
# for on message on different cogs

import asyncio
from enum import Enum
import re
import aiohttp
import discord
from discord.ext import commands
from discord import Embed, HTTPException, Webhook
import logging


log = logging.getLogger("globalchat.listener")


class MessageTypes(Enum):
    REPLY = "REPLY"
    DELETE = "DELETE"
    UPDATE = "UPDATE"
    SEND = "SEND"


class EventListeners(commands.Cog):
    def __init__(self, bot :commands.Bot, init, cacheManager):
        self.bot = bot
        self.init = init
        self.cache_manager = cacheManager


    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.id in self.init.bypass_delete_listener:
            return
        
        if message.author.bot: 
            return

        guild_id = message.guild.id
        channel_id = message.channel.id
        
        guild_document = self.init.find_guild(guild_id, channel_id)
        if not guild_document:
            return
        
        await self.validate_webhook_channel(message, guild_document, channel_id, MessageTypes.DELETE)

    @commands.Cog.listener()
    async def on_message_edit(self , before: discord.Message, after: discord.Message):
        if after.content.startswith(self.bot.command_prefix) or before.author.bot:
            return
        
        guild_id = before.guild.id
        channel_id = before.channel.id
        
        guild_document = self.init.find_guild(guild_id, channel_id)
        if not guild_document:
            return
        
        status, word = self.init.contains_malicious_url(after.content)
        if status:
            await after.delete()
            await after.author.send(embed = Embed(description="Your message contains malicious content. "
                                                              "Please refrain from using inappropriate language or sharing harmful links.\n\n"
                                                              f" Word: {word}"))    
            await self.init.log_report(after, "Editing Malicious Content")
            return
        await self.validate_webhook_channel(after, guild_document, channel_id, MessageTypes.UPDATE, before)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content.startswith(self.bot.command_prefix) or message.author.bot:
            return

        guild_id = message.guild.id
        channel_id = message.channel.id
        
        guild_document = self.init.find_guild(guild_id, channel_id)
        if not guild_document:
            return
        
        sender = self.bot.get_user(message.author.id)
        muted = self.init.isUserBlackListed(message.author.id)
        if muted:
            await message.delete()
            await sender.send(embed=Embed(description=f"You have been muted for {muted['reason']}"))
            return
        
        status, word = self.init.contains_malicious_url(message.content)
        if status:
            await message.delete()
            await message.author.send(embed = Embed(description="Your message contains malicious content. "
                                                                "Please refrain from using inappropriate language or sharing harmful links.\n\n"
                                                                f" Word: {word}"))    
            await self.init.log_report(message, "Sending Malicious Content")
            return
        
        if message.type == discord.MessageType.reply:
            messageType = MessageTypes.REPLY
        else:
            messageType = MessageTypes.SEND
        
        await self.validate_webhook_channel(message, guild_document, channel_id, messageType)


    async def validate_webhook_channel(self, message: discord.Message, guild_document, channel_id, messageType: MessageTypes,msg2 = None):
        # This function determines if where lobby should the message be sent    
        # Redundant need improvement 
        for channel in guild_document["channels"]:
            if channel["channel_id"] == channel_id and channel["webhook"]:    
                await self.send_to_matching_lobbies(message, channel['lobby_name'], channel_id, messageType, msg2)
            elif not channel["webhook"]:
                await message.channel.send("Re-register this channel for webhook registration")

    async def send_to_matching_lobbies(self, message: discord.Message, lobby_name, channel_id, messageType: MessageTypes, msg2 = None):
        # Prepare messagesData
        if messageType == MessageTypes.REPLY or messageType == MessageTypes.SEND:
            messagesData = {"source": message.id, "channel": message.channel.id, "author" : message.author.id,"webhooksent": []}
            embed = None
            source_data = None

            if message.reference and messageType == MessageTypes.REPLY:
                embed = await self.prepare_reply_embed(message, lobby_name)

        # Handles Delete and Update messages
        if messageType == MessageTypes.DELETE or messageType == MessageTypes.UPDATE:
            # Preparing Message_ID to use for delete / edit funciton

            # Getting source message in the cache
            source_data = self.cache_manager.find_source_data(message.id, lobby_name)

            # Combineing Message id since source_id is separated in to 
            # its webhooks send messages
            try:
                combined_ids = [
                    {"channel": source_data["channel"], 
                     "messageId": source_data["source"], 
                     "author" : source_data["author"]
                     }]
                
                combined_ids.extend(data for data in source_data["webhooksent"] if data["messageId"] != message.id)
            except TypeError as e:
                log.info(e)
            except UnboundLocalError as e:
                log.info(e)

            if msg2:
                await self.init.chat_log_report(message, MessageTypes.UPDATE, lobby_name, channel_id,msg2)
            else:
                await self.init.chat_log_report(message, MessageTypes.DELETE, lobby_name, channel_id)

        async with aiohttp.ClientSession() as session:
            tasks = []

            for document in self.init.guild_data:
                channels = document["channels"]
                for channel in channels:
                    # Checks if its not the guild and the channels via id basically filtered out the current channel
                    if channel["channel_id"] != channel_id and channel["lobby_name"] == lobby_name:
                        
                        try:
                            # webhook = self.create_webhook(channel["webhook"], session, messageType)
                            webhook  = Webhook.from_url(channel["webhook"], session=session)

                            if messageType == MessageTypes.SEND:
                                tasks.append(self.process_message(webhook,  message, messagesData))
                                
                            elif messageType == MessageTypes.REPLY: # Remove and combined_ids
                                # Reply Jump message
                                # view = await self.handle_reply(combined_ids, channel["channel_id"] )
                                tasks.append( self.process_message(webhook, message, messagesData, embed))

                            elif messageType == MessageTypes.DELETE and combined_ids:
                                channel_obj = await self.bot.fetch_channel(channel["channel_id"])
                                relative_message : discord.Message = await self.inti.find_messageID(channel_obj,combined_ids)
                                
                                tasks.append( self.process_edit_message(message,webhook, relative_message.id, messageType))
                            elif messageType == MessageTypes.UPDATE and combined_ids:
                                relative_message : discord.Message = await self.init.find_messageID(channel["channel_id"],combined_ids)
                                tasks.append( self.process_edit_message(message,webhook, relative_message.id, messageType))
                        except HTTPException as e:
                            if e.status == 429:
                                retry_after = int(e.response.headers['Retry-After'])
                                await asyncio.sleep(retry_after)
                                tasks.append(self.send_to_matching_lobbies(message, lobby_name, channel_id, messageType, msg2))
                        except UnboundLocalError as e:
                            log.warning(e)

            await asyncio.gather(*tasks)

            if messageType == MessageTypes.REPLY or messageType == MessageTypes.SEND:
                await self.cache_manager.cache_message(lobby_name, messagesData)

    async def process_message(self, webhook : Webhook, message : discord.Message, messagesData, embed = None):
        try:
            allowed_mentions = discord.AllowedMentions(everyone=False, users=False, roles=False)

            files = [await attachment.to_file() for attachment in message.attachments]
            
            # Generating user name
            modIcon = None
            for modData in self.init.moderator:
                for mod in modData["mods"]:
                    if mod["user_id"] == str(message.author.id):
                        modIcon = modData["icon"]
                        break
            
            if modIcon:  
                if hasattr(message.author,'global_name') and message.author.global_name:
                    username = f"{modIcon} {message.author.global_name} || {message.guild.name}"
                else:
                    username = f"{modIcon} {message.author.name} || {message.guild.name}"
            else:
                if hasattr(message.author,'global_name') and message.author.global_name:
                    username = f"{message.author.global_name} || {message.guild.name}"
                else:
                    username = f"{message.author.name} || {message.guild.name}"    

            # Check if the message contains a sticker
            if message.stickers and not embed:  # If there's a sticker and embed argument is not provided
                sticker = message.stickers[0]  # Assuming there's only one sticker in the message
                embed = discord.Embed(f"{message.author.global_name} || {message.guild.name} has sent a sticker")
                embed.set_image(url=sticker.url if hasattr(sticker, 'url') else sticker.image_url)
                content = message.content
            else:
                embed = embed  # Use provided embed
                content = message.content  # Use message content
    
            # Allows default avatar if theres none
            avatar_url = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
            
            wmsg : discord.WebhookMessage  = await webhook.send(
                content=  content,
                username= username,
                avatar_url= avatar_url,
                allowed_mentions=allowed_mentions,
                files=files,
                embed = embed,
                wait=True,
            )
            messagesData["webhooksent"].append({ "channel": wmsg.channel.id ,"messageId" : wmsg.id, "author" : wmsg.author.id})
        except KeyError as k:
            log.warning(k)
        except Exception as e:
            log.warning(e)

    async def process_reply(self,  webhook : Webhook, message : discord.Message, messagesData, embed, jump_url):
        try:
            allowed_mentions = discord.AllowedMentions(everyone=False, users=False, roles=False)

            files = [await attachment.to_file() for attachment in message.attachments]
            
            # Generating user name
            modIcon = None
            for modData in self.init.moderator:
                for mod in modData["mods"]:
                    if mod["user_id"] == str(message.author.id):
                        modIcon = modData["icon"]
                        break
            
            if modIcon:  
                if hasattr(message.author,'global_name') and message.author.global_name:
                    username = f"{modIcon} {message.author.global_name} || {message.guild.name}"
                else:
                    username = f"{modIcon} {message.author.name} || {message.guild.name}"
            else:
                if hasattr(message.author,'global_name') and message.author.global_name:
                    username = f"{message.author.global_name} || {message.guild.name}"
                else:
                    username = f"{message.author.name} || {message.guild.name}"    

            # TODO: Sticker this is not working
            # Check if the message contains a sticker
            if message.stickers and not embed:  # If there's a sticker and embed argument is not provided
                sticker = message.stickers[0]  # Assuming there's only one sticker in the message
                embed = discord.Embed(f"{message.author.global_name} || {message.guild.name} has sent a sticker")
                embed.set_image(url=sticker.url if hasattr(sticker, 'url') else sticker.image_url)
                content = message.content
            else:
                embed = embed  # Use provided embed
                content = message.content  # Use message content

            # Allows default avatar if theres none
            avatar_url = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
            
            if jump_url:
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Jump to message", style=discord.ButtonStyle.link, url= jump_url))
                
                wmsg : discord.WebhookMessage  = await webhook.send(
                    content=  content,
                    username= username,
                    avatar_url= avatar_url,
                    allowed_mentions=allowed_mentions,
                    files=files,
                    embed = embed,
                    view = view,
                    wait=True
                )
            else: 
                wmsg : discord.WebhookMessage  = await webhook.send(
                    content=  content,
                    username= username,
                    avatar_url= avatar_url,
                    allowed_mentions=allowed_mentions,
                    files=files,
                    embed = embed,
                    wait=True
                )
            
            messagesData["webhooksent"].append({ "channel": wmsg.channel.id ,"messageId" : wmsg.id, "author" : wmsg.author.id})

        except KeyError as k:
            log.warning(k)
        except Exception as e:
            log.warning(e)

    async def process_edit_message(self, message: discord.Message, webhook : Webhook, message_id, messageType):
        try:
            content = "*[message deleted by source]*"
            attachments = []
            embeds = []
            
            if messageType == MessageTypes.UPDATE:
                current_message = await webhook.fetch_message(message_id)
                content = current_message.content
                attachments = current_message.attachments
                embeds = current_message.embeds

                if message.content != current_message.content:
                    content = message.content
                if message.attachments != current_message.attachments:
                    attachments = message.attachments

            await webhook.edit_message(
                message_id,
                content=content,
                attachments=attachments,
                embeds=embeds
            )

        except Exception as e:
            log.warning(f"Failed to edit message {message.id}: {e}")
            log.warning(f"Failed to edit message {message.id}: {e}")
   

    
    

    def create_webhook(self, webhook_url, session, messageType):
        if messageType == MessageTypes.REPLY:
            match = re.match(r'https://discord.com/api/webhooks/(\d+)/(.+)', webhook_url)
            if not match:
                raise ValueError("Invalid webhook URL format")
            webhook_id, webhook_token = match.groups()
            return discord.Webhook.partial(id=int(webhook_id), token=webhook_token, session=session, client=self.bot)
        else:
            return discord.Webhook.from_url(webhook_url, session=session)
   
             
    async def prepare_reply_embed(self, message : discord.Message, lobby_name):
        replied_message = await message.channel.fetch_message(message.reference.message_id)
        embed = self.create_embed_for_message(replied_message)

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
    
    
    