"""The webhook-relay engine: takes a message sent/edited/deleted in a
connected channel and mirrors it across every other channel in the same
lobby via their webhooks.

`find_channel_in_document`, `prepare_reply_embed`, and
`build_relay_username` are plain functions — no Discord API calls, safe to
unit test directly. Everything else here does real webhook I/O and stays
on `RelayService`, which needs `bot` (to fetch channels) and
`cache_manager` (to look up which messages belong to the same relay chain).
"""
import asyncio
import logging
import re
from enum import Enum
from typing import List, Optional

import aiohttp
import discord
from discord import HTTPException, Webhook
from discord.ext import commands

log = logging.getLogger("globalchat.relay_service")


class MessageTypes(Enum):
    REPLY = "REPLY"
    DELETE = "DELETE"
    UPDATE = "UPDATE"
    SEND = "SEND"


def find_channel_in_document(documents: List[dict], current_channel: int) -> Optional[dict]:
    for doc in documents:
        if doc['channel'] == current_channel:
            return doc
    return None


def build_relay_username(author: discord.abc.User, guild_name: str) -> str:
    """The name a relayed message is shown under: the author's display name
    plus which server it came from. Deduplicates what used to be an
    identical block copy-pasted in both `process_message` and
    `process_reply`."""
    if getattr(author, 'global_name', None):
        return f"{author.global_name} || {guild_name}"
    return f"{author.name} || {guild_name}"


def prepare_reply_embed(replied_message: discord.Message) -> discord.Embed:
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


class RelayService:
    def __init__(self, bot: commands.Bot, state, cache_manager):
        self.bot = bot
        self.state = state
        self.cache_manager = cache_manager

    async def relay(self, message: discord.Message, connection: dict, message_type: MessageTypes):
        """Sends/edits/deletes `message` across every other channel
        connected to the same lobby as `connection`. Was `send_to_matching_lobbies`."""
        if message_type == MessageTypes.REPLY or message_type == MessageTypes.SEND:
            messages_data: List = []
            messages_data.append({
                "message_id": message.id,
                "channel": message.channel.id,
                "author": message.author.id,
                "source": True,
                "lobby_id": connection.lobby_id,
                })

            if message.reference and message_type == MessageTypes.REPLY:
                reply_message = await message.channel.fetch_message(message.reference.message_id)
                embed = prepare_reply_embed(reply_message)
                documents = self.cache_manager.find_source_by_message_id(message.reference.message_id, connection.lobby_id)

        # Handles Delete and Update messages
        if message_type == MessageTypes.DELETE or message_type == MessageTypes.UPDATE:

            documents = self.cache_manager.find_source_by_message_id(message.id, connection.lobby_id)

            if not documents:
                await message.channel.send(f"⚠️ Your message has passed {int(self.cache_manager.deleteMessageThreshold)/60} minutes, therefore I can't delete nor edit the message")
                return

            # TODO: Moderation — audit_log_service.chat_log_report, once
            # message moderation (issue 008) is wired back up here.

        async with aiohttp.ClientSession() as session:
            tasks = []

            for target_connection in self.state.connection:

                if target_connection.channel_id != message.channel.id and target_connection.lobby_id == connection.lobby_id:

                    try:
                        webhook = await self.create_webhook(target_connection.webhook, session, message_type)

                        if message_type == MessageTypes.SEND:
                            tasks.append(self.process_message(webhook, message, messages_data))

                        elif message_type == MessageTypes.REPLY:
                            reply_document = find_channel_in_document(documents, target_connection.channel_id) if documents else None
                            tasks.append(self.process_reply(webhook, message, messages_data, embed, reply_document))

                        elif message_type == MessageTypes.DELETE and documents:
                            relative_message = find_channel_in_document(documents, target_connection.channel_id)
                            tasks.append(self.process_edit_message(message, webhook, relative_message, message_type))

                        elif message_type == MessageTypes.UPDATE and documents:
                            relative_message = find_channel_in_document(documents, target_connection.channel_id)
                            tasks.append(self.process_edit_message(message, webhook, relative_message, message_type))

                    except HTTPException as e:
                        log.warning(e)
                    except UnboundLocalError as e:
                        log.warning(e)

            await asyncio.gather(*tasks)

        if message_type == MessageTypes.REPLY or message_type == MessageTypes.SEND:
            await self.cache_manager.cache_message(connection.lobby_id, messages_data)

    async def process_message(self, webhook: Webhook, message: discord.Message, messages_data, embed=None):
        try:
            allowed_mentions = discord.AllowedMentions(everyone=False, users=False, roles=False)

            files = [await attachment.to_file() for attachment in message.attachments]

            username = build_relay_username(message.author, message.guild.name)

            # Check if the message contains a sticker
            if message.stickers and not embed:  # If there's a sticker and embed argument is not provided
                sticker = message.stickers[0]  # Assuming there's only one sticker in the message
                embed = discord.Embed(f"{message.author.global_name} || {message.guild.name} has sent a sticker")
                embed.set_image(url=sticker.url if hasattr(sticker, 'url') else sticker.image_url)
                content = message.content
            else:
                content = message.content  # Use message content

            # Allows default avatar if theres none
            avatar_url = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url

            wmsg: discord.WebhookMessage = await webhook.send(
                content=content,
                username=username,
                avatar_url=avatar_url,
                allowed_mentions=allowed_mentions,
                files=files,
                embed=embed,
                wait=True,
            )

            messages_data.append({"channel": wmsg.channel.id, "message_id": wmsg.id, "author": wmsg.author.id, "source": False})
        except KeyError as k:
            log.warning(k)
        except Exception as e:
            log.warning(e)

    async def process_reply(self, webhook: Webhook, message: discord.Message, messages_data, embed, reply_document):
        try:
            allowed_mentions = discord.AllowedMentions(everyone=False, users=False, roles=False)

            files = [await attachment.to_file() for attachment in message.attachments]

            username = build_relay_username(message.author, message.guild.name)

            # TODO: Sticker this is not working
            if message.stickers and not embed:  # If there's a sticker and embed argument is not provided
                sticker = message.stickers[0]  # Assuming there's only one sticker in the message
                embed = discord.Embed(f"{message.author.global_name} || {message.guild.name} has sent a sticker")
                embed.set_image(url=sticker.url if hasattr(sticker, 'url') else sticker.image_url)
                content = message.content
            else:
                content = message.content  # Use message content

            # Allows default avatar if theres none
            avatar_url = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url

            # Try to fetch the reply url
            reply_message = None
            try:
                if reply_document['source'] != True:
                    reply_message: discord.WebhookMessage = await webhook.fetch_message(reply_document['message_id'])
                else:
                    channel = await self.bot.fetch_channel(reply_document['channel'])
                    reply_message = await channel.fetch_message(reply_document['message_id'])
            except Exception:
                reply_message = None

            if reply_document:

                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Jump to message", style=discord.ButtonStyle.link, url=reply_message.jump_url))

                wmsg: discord.WebhookMessage = await webhook.send(
                    content=content,
                    username=username,
                    avatar_url=avatar_url,
                    allowed_mentions=allowed_mentions,
                    files=files,
                    embed=embed,
                    view=view,
                    wait=True
                )
            else:
                wmsg: discord.WebhookMessage = await webhook.send(
                    content=content,
                    username=username,
                    avatar_url=avatar_url,
                    allowed_mentions=allowed_mentions,
                    files=files,
                    embed=embed,
                    wait=True
                )

            messages_data.append({"channel": wmsg.channel.id, "message_id": wmsg.id, "author": wmsg.author.id})

        except KeyError as k:
            log.warning(k)
        except Exception as e:
            log.warning(e)

    async def process_edit_message(self, message: discord.Message, webhook: Webhook, message_data, message_type):
        try:
            content = "*[message deleted by source]*"
            attachments = []
            embeds = []
            if message_type == MessageTypes.UPDATE:
                if message_data['source'] != True:
                    edited_message: discord.WebhookMessage = await webhook.fetch_message(message_data['message_id'])
                else:
                    channel = await self.bot.fetch_channel(message_data['channel'])
                    edited_message = await channel.fetch_message(message_data['message_id'])

                # This will retain if the message data ( content, attachements, embeds, etc.)
                content = edited_message.content
                attachments = edited_message.attachments
                embeds = edited_message.embeds

                if message.content != edited_message.content:
                    content = message.content

                if message.attachments != edited_message.attachments:
                    attachments = message.attachments

            await webhook.edit_message(
                message_data['message_id'],
                content=content,
                attachments=attachments,
                embeds=embeds
            )

        except Exception as e:
            log.warning(f"Failed to edit message {message.id}: {e}")

    async def create_webhook(self, webhook_url, session, message_type):
        if message_type == MessageTypes.REPLY:
            match = re.match(r'https://discord.com/api/webhooks/(\d+)/(.+)', webhook_url)
            if not match:
                raise ValueError("Invalid webhook URL format")
            webhook_id, webhook_token = match.groups()
            webhook = discord.Webhook.partial(id=int(webhook_id), token=webhook_token, session=session, client=self.bot)

        else:
            webhook = discord.Webhook.from_url(webhook_url, session=session)

        return webhook

    async def delete_relayed_message(self, lobby_id: str, message_id: int) -> bool:
        """Moderator-triggered delete: edits every relayed copy of
        `message_id` in `lobby_id` to a "deleted by moderator" placeholder.

        Returns False if the message isn't in the cache anymore (too old,
        or was never relayed). Was `Moderation.handle_delete_by_command` +
        `process_delete_message_by_mods`.
        """
        source_data = self.cache_manager.find_source_by_message_id(int(message_id), lobby_id)
        if not source_data:
            return False

        async with aiohttp.ClientSession() as session:
            tasks = []
            for connection in self.state.connection:
                if connection.lobby_id != lobby_id:
                    continue
                relative_message = find_channel_in_document(source_data, connection.channel_id)
                if relative_message:
                    webhook = await self.create_webhook(connection.webhook, session, MessageTypes.DELETE)
                    tasks.append(self._delete_as_moderator(webhook, relative_message))
            await asyncio.gather(*tasks)
        return True

    async def _delete_as_moderator(self, webhook: Webhook, message_data: dict):
        message_id = message_data['message_id']
        try:
            await webhook.edit_message(
                message_id,
                content="*[message deleted by moderator]*",
                attachments=[],
                embeds=[]
            )
        except Exception:
            # Not editable via webhook — this is the original, non-webhook
            # message. Delete it directly instead, bypassing the delete
            # listener so it doesn't try to relay this deletion too.
            try:
                self.state.bypass_delete_listener.add(message_id)
                channel = self.bot.get_channel(int(message_data['channel']))
                message = await channel.fetch_message(message_id)
                if message is None:
                    log.error(f"Message with ID {message_id} not found in channel {message_data['channel']}")
                    return

                content = message.content
                attachment_urls = [a.url for a in message.attachments]
                await message.delete()

                description = (
                    "Your message has been deleted by the moderator."
                    " Please be mindful of what you send.\n\n"
                    f"Content: {content}"
                )
                if attachment_urls:
                    description += "\n\nAttachments:\n" + "\n".join(attachment_urls)

                embed = discord.Embed(description=description)
                if attachment_urls:
                    embed.set_image(url=attachment_urls[0])

                await message.author.send(embed=embed)
            except Exception as inner_e:
                log.warning(f"Failed to fetch or edit message: {inner_e}")
            finally:
                self.state.bypass_delete_listener.discard(message_id)
