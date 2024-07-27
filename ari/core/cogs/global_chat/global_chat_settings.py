import asyncio
import discord
import logging

from typing import List
from discord import app_commands
from discord.ext import commands

from .global_chat_ui_views import DynamicChoice, DynamicDropDown

from ...utils.utility import Color

log = logging.getLogger('global.settings')

class Config(commands.Cog):
    def __init__(self, bot, init) -> None:
        super().__init__()
        self.bot = bot
        self.init = init
        self.fields = [ {
            "title": "Lobby Details",
            "description": "<:_blank:1266299283737677844>Edit",
            "value": "lobbydetails",
            "emoji": "🔎",
            "inline": True
            },
            {
            "title": "Moderation",
            "description": "<:_blank:1266299283737677844>Change",
            "value": "moderation",
            "emoji": "🛠️",
            "inline": True
            },
            {
            "title": "Logging",
            "description": "<:_blank:1266299283737677844>Change",
            "value": "logging",
            "emoji": "📝",
            "inline": True
            }
        ]
        # settings 
        self.sent_message = None

    async def settings_autocompletion(
            self,
            interaction: discord.Interaction,
            current: str
        ) -> List[app_commands.Choice[str]]:

            # List top-level commands for auto-completion, excluding specific commands
            settings_choices = [
                app_commands.Choice(name=fields['title'], value=fields['value'])
                for fields in self.fields
            ]

            # Combine and limit the number of choices to 25 or fewer
            return settings_choices
    
    # We'll be having a config file for this for each lobby
    @commands.hybrid_command(name="settings", with_app_command=True ,description="Shows and configure lobby settings")
    @app_commands.autocomplete(settings=settings_autocompletion)
    async def settings(
        self, 
        ctx:commands.Context, 
        settings: str = None
        ):
        # Need validation if he's an owner and will pick a which lobby is this
        if self.sent_message is not None:
            await self.settings_menu(ctx, True)
            
        log.info(self.sent_message)
        if not settings:
            settings = await self.settings_menu(ctx)
            
        await self.setting_manager(settings, ctx)

        log.info(self.sent_message)
        self.sent_message = None

    async def setting_manager(
            self, 
            choice, 
            ctx : commands.Context, 
        ):
        flag = choice

        while True:
            if str(choice) == "lobbydetails":
                flag = await self.lobby_details(ctx)
            elif str(choice) == "moderation":
                flag = await self.moderation(ctx)
            elif str(choice) == "logging":
                flag = await self.lobby_logging(ctx)
            else:
                embed = self.create_embed(
                    "Not Found", 
                    "Settings not found"
                    )     
                await ctx.interaction.response.defer()
                await ctx.send(embed=embed)
                return
            
            if str(flag) == "Back":
                flag = await self.settings_menu(ctx)

            if flag is None:
                break
        
    async def settings_menu(self, ctx:commands.Context, delete: bool = False):
        embed = self.create_embed(
            "Settings", 
            "Shows and configure lobby settings",
            self.fields
            )            
        views = DynamicDropDown(
            ctx.message.author,
            self.fields,
            "⚙️ Setting"
            )
        if not delete:
            if self.sent_message is not None:
                await self.sent_message.edit(embed=embed, view=views)
            else:
                self.sent_message = await ctx.send(embed=embed, view=views)
        else:
            await self.sent_message.edit(embed=embed)
            self.sent_message = None

        try:
            await asyncio.wait_for(views.wait(), timeout=180)
        except asyncio.TimeoutError:
            await self.sent_message.edit(embed=embed,view=None)
            return None

        return views.value  
    
    def create_embed(self, title, description=None ,fields=None):
        embed = discord.Embed(color=Color.PRIMARY.to_discord_color(),description= description)
        embed.set_author(name=f"Ari connect - {title}", icon_url=self.bot.user.avatar.url)
        
        if fields:
            for field in fields:
                embed.add_field(name=f"{field['emoji']} {field['title']}", value=field['description'], inline=field['inline'])

        return embed        
    
    async def lobby_details(self, ctx:commands.Context):
        fields = [
            {
            "title": "Title",
            "description": "<:_blank:1266299283737677844> placeholder actual value",
            "value": "title",
            "emoji": "💬",
            "inline": False
            },
            {
            "title": "Description",
            "description": "<:_blank:1266299283737677844> placeholder actual value",
            "value": "description",
            "emoji": "📝",
            "inline": False
            },
            {
            "title": "Topics",
            "description": "<:_blank:1266299283737677844> placeholder actual value",
            "value": "topics",
            "emoji": "🔎",
            "inline": False
            }
        ]
        embed = self.create_embed(
            title = "Lobby Details",
            fields = fields
            )       
        # TODO: Can keep interacting after I press back button
        views = DynamicChoice(
            ctx.message.author,
            ['Back', 'Choice1','Choice2']
        )
        if self.sent_message is not None:
            await self.sent_message.edit(embed=embed, view=views)
        else:
            self.sent_message = await ctx.send(embed=embed, view=views)

        try:
            await asyncio.wait_for(views.wait(), timeout=180)
        except asyncio.TimeoutError:
            await self.sent_message.edit(embed=embed, view=None)
            return None
        
        return

    async def moderation(self, ctx:commands.Context, msg:discord.Message = None):
        fields = [
            {
            "title": "Moderators",
            "description": "<:_blank:1266299283737677844> placeholder actual value : number",
            "value": "moderators",
            "emoji": "🛡️",
            "inline": False
            }
        ]
        embed = self.create_embed(
            title = "Moderation",
            fields = fields
            )       
        # TODO: Can keep interacting after I press back button
        views = DynamicChoice(
            ctx.message.author,
            ['Back', 'Choice1','Choice2']
        )
        if self.sent_message is not None:
            await self.sent_message.edit(embed=embed, view=views)
        else:
            self.sent_message = await ctx.send(embed=embed, view=views)

        try:
            await asyncio.wait_for(views.wait(), timeout=180)
        except asyncio.TimeoutError:
            await self.sent_message.edit(embed=embed, view=None)
            return None
        
        return

    async def lobby_logging(self, ctx:commands.Context, msg:discord.Message = None):
        fields = [
            {
            "title": "Chat Logs",
            "description": "<:_blank:1266299283737677844> placeholder actual value",
            "value": "chatlogs",
            "emoji": "💬",
            "inline": True
            },
            {
            "title": "Moderation Logs",
            "description": "<:_blank:1266299283737677844> placeholder actual value",
            "value": "moderationlogs",
            "emoji": "📝",
            "inline": True
            },
            {
            "title": "Report Logs",
            "description": "<:_blank:1266299283737677844> placeholder actual value",
            "value": "reportlogs",
            "emoji": "🔎",
            "inline": True
            }
        ]
        embed = self.create_embed(
            title = "Logging",
            fields = fields
            )       
        # TODO: Can keep interacting after I press back button
        views = DynamicChoice(
            ctx.message.author,
            ['Back', 'Choice1','Choice2']
        )
        if self.sent_message is not None:
            await self.sent_message.edit(embed=embed, view=views)
        else:
            self.sent_message = await ctx.send(embed=embed, view=views)

        try:
            await asyncio.wait_for(views.wait(), timeout=180)
        except asyncio.TimeoutError:
            await self.sent_message.edit(embed=embed, view=None)
            return None
        
        return

        