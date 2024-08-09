import asyncio
import discord
import logging

from typing import List
from discord import app_commands
from discord.ext import commands

from .global_chat_ui_views import DynamicChoice, DynamicDropDown
from .global_chat_initialization import Intialization
from ...utils.utility import Color

log = logging.getLogger('global.settings')

class Config(commands.Cog):
    def __init__(self, bot: commands.Bot, init: Intialization) -> None:
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
        settings = None,
        lobby_id = None
        ):
        owner = ctx.message.author.id
        lobby_config = None
        isOwner = False

        # Validation
        if not lobby_id:
            lobbies_owned = []
            # Look for the owned lobbies and list them all
            for lobby_data in self.init.lobby_data:
                if lobby_data["owner_id"] == owner:
                    lobbies_owned.append(lobby_data)

            if len(lobbies_owned) > 0:
                # List lobbbies, with a dropdown
                dropdown_data = []
                list_embed_data = ""
                embed = discord.Embed(title="Available lobbies")
                # TODO: This could be improve by using inheritance lobby_config inherits lobby
                for data in lobbies_owned:
                    for lobby_config in self.init.lobby_config:
                        if lobby_config['lobby_id'] == data['lobby_id']:
                            dropdown_data.append({
                                'title' :  lobby_config['lobby_config']['title'],
                                'value' : data['lobby_id']
                            })
                            list_embed_data += f"**{lobby_config['lobby_config']['title']}**\n lobby_id: {lobby_config['lobby_id']}\n\n"
                            break
                await ctx.send()
                # then from there thats the config that we gonna use 
                pass
            else:
                await ctx.send(embed=discord.Embed(description="You dont owned any lobbies"))
        else:
            # Validate if he's the owner
            for lobby_data in self.init.lobby_data:
                if lobby_data['owner_id'] == owner:
                    isOwner = True

            if not isOwner:
                await ctx.send(embed=discord.Embed("You don't owned this lobby"))
            
            # look for lobby config that the owner owned
            for config in self.init.lobby_config:
                if config['lobby_id'] == lobby_id:
                    lobby_config = config
                    break        


        if self.sent_message is not None:
            await self.settings_menu(ctx, True)
            
        if not settings:
            settings = await self.settings_menu(ctx)
            
        await self.setting_manager(settings, ctx, lobby_config)

    async def setting_manager(
            self, 
            choice, 
            ctx : commands.Context,
            lobby_config 
        ):
        flag = choice

        while True:
            if str(flag) == "lobbydetails":
                flag = await self.lobby_details(ctx, lobby_config['lobby_config'])
            elif str(flag) == "moderation":
                flag = await self.moderation(ctx, lobby_config['moderation_config'])
            elif str(flag) == "logging":
                flag = await self.lobby_logging(ctx, lobby_config['log_config'])
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
          
    async def settings_menu(self, ctx:commands.Context ,delete: bool = False) -> (str | None):
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
            await self.sent_message.edit(embed=self.sent_message.embeds[0], view=None)
            self.sent_message = None
            return None
    
    def create_embed(self, title, description=None ,fields=None) -> discord.Embed:
        embed = discord.Embed(color=Color.PRIMARY.to_discord_color(),description= description)
        embed.set_author(name=f"Ari connect - {title}", icon_url=self.bot.user.avatar.url)
        
        if fields:
            for field in fields:
                embed.add_field(name=f"{field['emoji']} {field['title']}", value=field['description'], inline=field['inline'])

        return embed        
    
    async def lobby_details(self, ctx:commands.Context, lobby_details) -> (str | None):
        fields = [
            {
            "title": "Title",
            "description": f"<:_blank:1266299283737677844>{lobby_details['title']}",
            "value": "title",
            "emoji": "💬",
            "inline": False
            },
            {
            "title": "Description",
            "description": f"<:_blank:1266299283737677844> {lobby_details['description']}",
            "value": "description",
            "emoji": "📝",
            "inline": False
            },
            {
            "title": "Topics",
            "description": f"<:_blank:1266299283737677844> {lobby_details['topics']}",
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
                            # Maybe the embed or something
                            
                            # ==============================================================================================
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

    async def moderation(self, ctx:commands.Context, moderation_config, msg:discord.Message = None):
        fields = [
            {
            "title": "Moderators",
            "description": f"<:_blank:1266299283737677844> {len(moderation_config['moderators'])}",
            "value": "moderators",
            "emoji": "🛡️",
            "inline": False
            },
            {
            "title": "Banned Words",
            "description": f"<:_blank:1266299283737677844> {len(moderation_config['banned_words'])}",
            "value": "bannedwords",
            "emoji": "💬",
            "inline": False
            },
            {
            "title": "Banned Links",
            "description": f"<:_blank:1266299283737677844> {len(moderation_config['banned_links'])}",
            "value": "bannedlinks",
            "emoji": "🔗",
            "inline": False
            },
            {
            "title": "Banned users",
            "description": f"<:_blank:1266299283737677844> {len(moderation_config['banned_users'])}",
            "value": "bannedusers",
            "emoji": "👤",
            "inline": False
            },
            {
            "title": "Banned servers",
            "description": f"<:_blank:1266299283737677844> {len(moderation_config['banned_servers'])}",
            "value": "bannedservers",
            "emoji": "🌐",
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
                    case 'Banned Words':
                        # This handles if its clicked, so it change the color and the send the message
                        if button_interaction_data[2]['status'] is not True:
                            button_interaction_data[2]['color'] = discord.ButtonStyle.primary
                            # ==============================================================================================
                            # Some setting logic will happen here before sending


                            # ==============================================================================================
                            button_interaction_data[2]['sent_message'] = await ctx.send('Rendering Input button for Banned Words')
                        # Then if handles if message was sent so we delete it and change the color to gray
                        else:
                            button_interaction_data[2]['color'] = discord.ButtonStyle.grey
                            await button_interaction_data[2]['sent_message'].delete()
                            
                            button_interaction_data[2]['sent_message'] = None

                        button_interaction_data[2]['status'] = not button_interaction_data[2]['status']
                    case 'Banned Links':
                        # This handles if its clicked, so it change the color and the send the message
                        if button_interaction_data[3]['status'] is not True:
                            button_interaction_data[3]['color'] = discord.ButtonStyle.primary
                            # ==============================================================================================
                            # Some setting logic will happen here before sending


                            # ==============================================================================================
                            button_interaction_data[3]['sent_message'] = await ctx.send('Rendering Input button for Banned Links')
                        # Then if handles if message was sent so we delete it and change the color to gray
                        else:
                            button_interaction_data[3]['color'] = discord.ButtonStyle.grey
                            await button_interaction_data[3]['sent_message'].delete()
                            
                            button_interaction_data[3]['sent_message'] = None

                        button_interaction_data[3]['status'] = not button_interaction_data[3]['status']
                    case 'Banned users':
                        # This handles if its clicked, so it change the color and the send the message
                        if button_interaction_data[4]['status'] is not True:
                            button_interaction_data[4]['color'] = discord.ButtonStyle.primary
                            # ==============================================================================================
                            # Some setting logic will happen here before sending


                            # ==============================================================================================
                            button_interaction_data[4]['sent_message'] = await ctx.send('Rendering Input button for Banned users')
                        # Then if handles if message was sent so we delete it and change the color to gray
                        else:
                            button_interaction_data[4]['color'] = discord.ButtonStyle.grey
                            await button_interaction_data[4]['sent_message'].delete()
                            
                            button_interaction_data[4]['sent_message'] = None

                        button_interaction_data[4]['status'] = not button_interaction_data[4]['status']
                    case 'Banned servers':
                        # This handles if its clicked, so it change the color and the send the message
                        if button_interaction_data[5]['status'] is not True:
                            button_interaction_data[5]['color'] = discord.ButtonStyle.primary
                            # ==============================================================================================
                            # Some setting logic will happen here before sending


                            # ==============================================================================================
                            button_interaction_data[5]['sent_message'] = await ctx.send('Rendering Input button for Banned servers')
                        # Then if handles if message was sent so we delete it and change the color to gray
                        else:
                            button_interaction_data[5]['color'] = discord.ButtonStyle.grey
                            await button_interaction_data[5]['sent_message'].delete()
                            
                            button_interaction_data[5]['sent_message'] = None

                        button_interaction_data[5]['status'] = not button_interaction_data[5]['status']

                    case _:
                        return None


                # Recreate view and reset wait
                views = DynamicChoice(ctx.message.author, button_interaction_data)
                await self.sent_message.edit(view=views)

            except asyncio.TimeoutError:
                return None

    async def lobby_logging(self, ctx:commands.Context, logging_config,msg:discord.Message = None):
        fields = [
            {
            "title": "Chat Logs",
            "description": f"<:_blank:1266299283737677844> {logging_config['chat_log']['channel_id']}", # This is a conditional like if the channel_id has value then set it to true else false
            "value": "chatlogs",
            "emoji": "💬",
            "inline": True
            },
            {
            "title": "Moderation Logs",
            "description": f"<:_blank:1266299283737677844> {logging_config['moderation_logs']['channel_id']}",
            "value": "moderationlogs",
            "emoji": "📝",
            "inline": True
            },
            {
            "title": "Report Logs",
            "description": f"<:_blank:1266299283737677844> {logging_config['report_logs']['channel_id']}",
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
        