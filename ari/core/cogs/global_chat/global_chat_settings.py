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
        self.sent_message : discord.Message = None

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
        settings: str = None,
        ):
        # Need validation if he's an owner and will pick a which lobby is this
        if self.sent_message is not None:
            await self.settings_menu(ctx, True)
            
        if not settings:
            settings = await self.settings_menu(ctx)
            
        await self.setting_manager(settings, ctx)

    async def setting_manager(
            self, 
            choice, 
            ctx : commands.Context, 
        ):
        flag = choice

        while True:
            if str(flag) == "lobbydetails":
                flag = await self.lobby_details(ctx)
            elif str(flag) == "moderation":
                flag = await self.moderation(ctx)
            elif str(flag) == "logging":
                flag = await self.lobby_logging(ctx)
            else:
                embed = self.create_embed(
                    "Not Found", 
                    "Settings not found"
                    )     
                await ctx.interaction.response.defer()
                await ctx.send(embed=embed)
                return
            
            if flag is None:
                await self.settings_menu(ctx, True)
                break

            if str(flag) == "Back" or flag:
                flag = await self.settings_menu(ctx)
          
    async def settings_menu(self, ctx:commands.Context, delete: bool = False) -> (str | None):
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

            try:
                await asyncio.wait_for(views.wait(), timeout=180)
            except asyncio.TimeoutError:
                await self.sent_message.edit(embed=embed,view=None)
                self.sent_message=None
                return None

            return views.value  

        else:
            await self.sent_message.edit(embed=embed, view=None)
            self.sent_message = None
            return None
    
    def create_embed(self, title, description=None ,fields=None) -> discord.Embed:
        embed = discord.Embed(color=Color.PRIMARY.to_discord_color(),description= description)
        embed.set_author(name=f"Ari connect - {title}", icon_url=self.bot.user.avatar.url)
        
        if fields:
            for field in fields:
                embed.add_field(name=f"{field['emoji']} {field['title']}", value=field['description'], inline=field['inline'])

        return embed        
    
    async def lobby_details(self, ctx:commands.Context) -> (str | None):
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
        button_interaction_data = [
            {
            'title':'Back',
            'color': discord.ButtonStyle.grey,
            'status': False,
            'sent_message': None
            }, 
            {
            'title':'Title',
            'color': discord.ButtonStyle.grey,
            'status': False,
            'sent_message': None
            },
            {
            'title':'Description',
            'color': discord.ButtonStyle.grey,
            'status': False,
            'sent_message': None
            },
            {
            'title':'Topics',
            'color': discord.ButtonStyle.grey,
            'status': False,
            'sent_message': None
            }
        ]
             
        # TODO: Can keep interacting after I press back button
        views = DynamicChoice(
            ctx.message.author,
            button_interaction_data
        )
                    

        if self.sent_message is not None:
            await self.sent_message.edit(embed=embed, view=views)
        else:
            self.sent_message = await ctx.send(embed=embed, view=views)
        # TODO: Refactor this
        while True:
            try:
                await views.wait()
                value = views.value
                
                match value:
                    case 'Back':
                        # Delete all 
                        for button_data in button_interaction_data:
                            if button_data['status'] is True:
                                await button_data['sent_message'].delete()
                        return 'Back'
                    case 'Title':
                        # This handles if its clicked, so it change the color and the send the message
                        if button_interaction_data[1]['status'] is not True:
                            button_interaction_data[1]['color'] = discord.ButtonStyle.primary
                            # ==============================================================================================
                            # Some setting logic will happen here before sending


                            # ==============================================================================================
                            button_interaction_data[1]['sent_message'] = await ctx.send('Rendering Input button for Title')
                        # Then if handles if message was sent so we delete it and change the color to gray
                        else:
                            button_interaction_data[1]['color'] = discord.ButtonStyle.grey
                            await button_interaction_data[1]['sent_message'].delete()
                            
                            button_interaction_data[1]['sent_message'] = None

                        button_interaction_data[1]['status'] = not button_interaction_data[1]['status']

                    case 'Description':
                        # This handles if its clicked, so it change the color and the send the message
                        if button_interaction_data[2]['status'] is not True:
                            button_interaction_data[2]['color'] = discord.ButtonStyle.primary
                            button_interaction_data[2]['sent_message'] = await ctx.send('Rendering Input button for Description')
                        # Then if handles if message was sent so we delete it and change the color to gray
                        else:
                            button_interaction_data[2]['color'] = discord.ButtonStyle.grey
                            await button_interaction_data[2]['sent_message'].delete()
                            
                            button_interaction_data[2]['sent_message'] = None

                        button_interaction_data[2]['status'] = not button_interaction_data[2]['status']
                    case 'Topics':
                        # This handles if its clicked, so it change the color and the send the message
                        if button_interaction_data[3]['status'] is not True:
                            button_interaction_data[3]['color'] = discord.ButtonStyle.primary
                            button_interaction_data[3]['sent_message'] = await ctx.send('Rendering Input button for Topics')
                        # Then if handles if message was sent so we delete it and change the color to gray
                        else:
                            button_interaction_data[3]['color'] = discord.ButtonStyle.grey
                            await button_interaction_data[3]['sent_message'].delete()
                            
                            button_interaction_data[3]['sent_message'] = None

                        button_interaction_data[3]['status'] = not button_interaction_data[3]['status']
                    case _:
                        return None


                # Recreate view and reset wait
                views = DynamicChoice(ctx.message.author, button_interaction_data)
                await self.sent_message.edit(view=views)

            except asyncio.TimeoutError:
                return None

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
        button_interaction_data = [
            {
            'title':'Back',
            'color': discord.ButtonStyle.grey,
            'status': False,
            'sent_message': None
            }, 
            {
            'title':'Moderators',
            'color': discord.ButtonStyle.grey,
            'status': False,
            'sent_message': None
            }
        ]
             
        # TODO: Can keep interacting after I press back button
        views = DynamicChoice(
            ctx.message.author,
            button_interaction_data
        )
                    

        if self.sent_message is not None:
            await self.sent_message.edit(embed=embed, view=views)
        else:
            self.sent_message = await ctx.send(embed=embed, view=views)
        # TODO: Refactor this
        while True:
            try:
                await views.wait()
                value = views.value
                
                match value:
                    case 'Back':
                        # Delete all 
                        for button_data in button_interaction_data:
                            if button_data['status'] is True:
                                await button_data['sent_message'].delete()
                        return 'Back'
                    case 'Moderators':
                        # This handles if its clicked, so it change the color and the send the message
                        if button_interaction_data[1]['status'] is not True:
                            button_interaction_data[1]['color'] = discord.ButtonStyle.primary
                            # ==============================================================================================
                            # Some setting logic will happen here before sending


                            # ==============================================================================================
                            button_interaction_data[1]['sent_message'] = await ctx.send('Rendering Input button for Moderators')
                        # Then if handles if message was sent so we delete it and change the color to gray
                        else:
                            button_interaction_data[1]['color'] = discord.ButtonStyle.grey
                            await button_interaction_data[1]['sent_message'].delete()
                            
                            button_interaction_data[1]['sent_message'] = None

                        button_interaction_data[1]['status'] = not button_interaction_data[1]['status']
                    case _:
                        return None


                # Recreate view and reset wait
                views = DynamicChoice(ctx.message.author, button_interaction_data)
                await self.sent_message.edit(view=views)

            except asyncio.TimeoutError:
                return None

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
        button_interaction_data = [
            {
            'title':'Back',
            'color': discord.ButtonStyle.grey,
            'status': False,
            'sent_message': None
            }, 
            {
            'title':'Chat Logs',
            'color': discord.ButtonStyle.grey,
            'status': False,
            'sent_message': None
            },
            {
            'title':'Moderation Logs',
            'color': discord.ButtonStyle.grey,
            'status': False,
            'sent_message': None
            },
            {
            'title':'Report Logs',
            'color': discord.ButtonStyle.grey,
            'status': False,
            'sent_message': None
            }
        ]
             
        # TODO: Can keep interacting after I press back button
        views = DynamicChoice(
            ctx.message.author,
            button_interaction_data
        )
                    

        if self.sent_message is not None:
            await self.sent_message.edit(embed=embed, view=views)
        else:
            self.sent_message = await ctx.send(embed=embed, view=views)
        # TODO: Refactor this
        while True:
            try:
                await views.wait()
                value = views.value
                
                match value:
                    case 'Back':
                        # Delete all 
                        for button_data in button_interaction_data:
                            if button_data['status'] is True:
                                await button_data['sent_message'].delete()
                        return 'Back'
                    case 'Chat Logs':
                        # This handles if its clicked, so it change the color and the send the message
                        if button_interaction_data[1]['status'] is not True:
                            button_interaction_data[1]['color'] = discord.ButtonStyle.primary
                            # ==============================================================================================
                            # Some setting logic will happen here before sending


                            # ==============================================================================================
                            button_interaction_data[1]['sent_message'] = await ctx.send('Rendering Input button for Chat Logs')
                        # Then if handles if message was sent so we delete it and change the color to gray
                        else:
                            button_interaction_data[1]['color'] = discord.ButtonStyle.grey
                            await button_interaction_data[1]['sent_message'].delete()
                            
                            button_interaction_data[1]['sent_message'] = None

                        button_interaction_data[1]['status'] = not button_interaction_data[1]['status']

                    case 'Moderation Logs':
                        # This handles if its clicked, so it change the color and the send the message
                        if button_interaction_data[2]['status'] is not True:
                            button_interaction_data[2]['color'] = discord.ButtonStyle.primary
                            button_interaction_data[2]['sent_message'] = await ctx.send('Rendering Input button for Moderation Logs')
                        # Then if handles if message was sent so we delete it and change the color to gray
                        else:
                            button_interaction_data[2]['color'] = discord.ButtonStyle.grey
                            await button_interaction_data[2]['sent_message'].delete()
                            
                            button_interaction_data[2]['sent_message'] = None

                        button_interaction_data[2]['status'] = not button_interaction_data[2]['status']
                    case 'Report Logs':
                        # This handles if its clicked, so it change the color and the send the message
                        if button_interaction_data[3]['status'] is not True:
                            button_interaction_data[3]['color'] = discord.ButtonStyle.primary
                            button_interaction_data[3]['sent_message'] = await ctx.send('Rendering Input button for Report Logs')
                        # Then if handles if message was sent so we delete it and change the color to gray
                        else:
                            button_interaction_data[3]['color'] = discord.ButtonStyle.grey
                            await button_interaction_data[3]['sent_message'].delete()
                            
                            button_interaction_data[3]['sent_message'] = None

                        button_interaction_data[3]['status'] = not button_interaction_data[3]['status']
                    case _:
                        return None


                # Recreate view and reset wait
                views = DynamicChoice(ctx.message.author, button_interaction_data)
                await self.sent_message.edit(view=views)

            except asyncio.TimeoutError:
                return None
        