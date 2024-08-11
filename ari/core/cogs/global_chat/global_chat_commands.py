import asyncio
import logging
import aiohttp
import discord
from discord.ext import commands
from discord import Embed, Webhook

import discord.ext
import discord.ext.commands
from .global_chat_ui_views import CreateLobbyModal, LobbyPagination, DynamicDropDown
from .global_chat_initialization import Intialization
from ...utils.utility import Color
log = logging.getLogger("globalchat.commands")

class Chat(commands.Cog):
    def __init__(self, bot : commands.Bot, initialization : Intialization, repositories):
        self.bot = bot
        self.init = initialization
        self.repos = repositories

    # Conditions: Perms to kick user
    @commands.hybrid_command(name='createlobby',with_app_command=True, description='Create a global chat lobby, 1 per server')
    @commands.has_permissions(kick_members=True)
    async def createLobby(self, ctx:commands.Context):
        
        guild_id = ctx.guild.id
        canCreate = False
        
        for id in self.init.lobby_data:
            if guild_id == id["guild_id"]:
                log.info(id)
                canCreate = True
                break
            
        if not canCreate:               
            modal = CreateLobbyModal(self.init.lobby_data,self.init.connection,self.init.lobby_config)
            response = await ctx.interaction.response.send_modal(modal) 
        else:
            await ctx.send(embed=discord.Embed( description= ":no_entry: You have reached the limit of 1 lobby per server",  color=0xFFC0CB))


    @commands.hybrid_command(name='lobby_show', description="Shows more information of the lobby using the code")
    async def showlobbyData(self, ctx: commands.Context, lobby_id: str):

        guild = ctx.guild
        channel = ctx.channel

        lobby = self.init.isLobbyExists(lobby_id)

        if not lobby:
            await ctx.send(embed=discord.Embed( description= "lobby doesnt exists",  color=0xFFC0CB))

        data = self.init.get_lobby_basic_data(lobby_id)

        # Fetch guild information
        guild_data  = await self.bot.fetch_guild(data["guild_id"])

        # Preparing embed for view
 
        embed = discord.Embed(
            title= data['title'], 
            color=0xFFC0CB
        )

        embed.set_thumbnail(url=str(guild_data.icon.url))
        embed.add_field(name="Host", value=f"**Name:** {guild_data.name} \n**Members:** {guild_data.approximate_member_count}", inline=True)
        embed.add_field(
            name="Info", 
            value= f"Connections: `{self.init.get_lobby_length(data['lobby_id'])}/{data['limit']}` \n"
                    f" Lobby code: {data['lobby_id']}",
            inline=True)
                
        topics = ""
        for topic in data["topics"]:
            topics += f"`{topic}` "

        embed.add_field(name="Topics", value=topics, inline=False)
        embed.add_field(name="Description", value=data['description'], inline=False)


        connections = self.init.get_lobby_connections(data['lobby_id'])
        format = ""
        limit = 1
        for conn in connections:
            if limit > 10:
                break
            else:
                format += f"{conn["guild_name"]}\n"
                limit += 1

        embed.add_field(name="Connections", value=format, inline=False)
        embed.set_footer(text=data['footer_message'])
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='lobbies', description='Current Lobby description')
    async def show_lobbies(self, ctx: commands.Context):
        
        available_lobbies = self.init.get_all_lobby_data()
        view = LobbyPagination(
            data=available_lobbies,
            title= "Open Lobbies",
            author= ctx.message.author,
            addional_info_field= True
        )

        await view.send(ctx)

    @commands.hybrid_command(name='connect', description='Link to Open World')
    @commands.has_permissions(kick_members=True)
    async def openworldlink(self, ctx : commands.Context, lobby_id: str = None):

        # Gather necessary variables in the command        
        guild = ctx.guild
        channel = ctx.channel
        data = None

        # Validate connection
        connection = self.init.get_connection(channel.id,guild.id)
        
        if connection:
            embed = Embed(
                title=":no_entry: Your channel is already registered for Open World Chat",
                description="Type `a!unlink` to unlink your Open World\n*This will only unlink from the Open World channel*",
                color=0xFF0000  # Red color
            )
            await ctx.send(embed=embed)
            return 
        
        if lobby_id:
            # If provided create data for connection
            lobby_data = self.init.isLobbyExists(lobby_id)

            if not lobby_data:
                embed = Embed(
                    title="The lobby ID that you have provided is not available",
                    color=0xFF0000  # Red color
                    )
                await ctx.send(embed=embed)
                return 
            # Get Lobby Config for details such as limit
            data = self.init.get_lobby_basic_data(lobby_id)

            # Check the limit
            current = self.init.get_lobby_length(lobby_id)

            if current >= data['limit']:
                embed = Embed(
                    title=" Lobby is full",
                    color=0xFF0000  # Red color
                )
                await ctx.send(embed=embed)
                return
        else:
            # If not provided auto show lobbies
            available_lobbies = self.init.get_all_lobby_data()
            
            views = LobbyPagination(
                data = available_lobbies,
                title = "Available Lobbies",
                author= ctx.message.author,
                addional_info_field= False,
                add_dropdown= True,
                drop_placeholder= "Select lobby"
            )
            await views.send(ctx)
            try:
                await asyncio.wait_for(views.wait(), timeout=60)
            except asyncio.TimeoutError:
                await views.message.edit(view=None)
            
            selected_val = views.value

            if selected_val == "Back":
                await views.message.edit(view=None)
                return
            
            data = self.init.get_lobby_basic_data(selected_val)

            current = self.init.get_lobby_length(data['lobby_id'])

            if current >= data['limit']:
                embed = Embed(
                    title=":no_entry: Lobby is full",
                    color=0xFF0000  # Red color
                )
                await ctx.send(embed=embed)
                return
            
        # Create a connection and save it to cache
        webhook = await channel.create_webhook(name=data['title'])
        connection_data = {
            "lobby_id": data["lobby_id"],
            "channel_id": channel.id,
            "webhook": webhook.url,
            "guild_id": guild.id,
            "guild_name": guild.name
        }

        res = await self.repos.guild_repository.create(connection_data)
        connection_data['_id'] =res.inserted_id
        
        self.init.connection.append(connection_data)

        # Send a success message if its successfull
        embed = Embed(
            description=f':white_check_mark: **LINK START!! You are now connected to {data['title']}**',
            color=0x7289DA 
        )
        
        await ctx.send(embed=embed)

        await asyncio.sleep(1)

        embed = Embed(
            title="Thank you for linking with Open World Server!",
            description= self.init.openworldThanksMessage,
            color=0x00FF00 
        )

        message = await ctx.send(embed=embed)

        await message.add_reaction('✅')

        await self.on_join_announce(ctx, connection_data['lobby_id'])
       
        
    @commands.hybrid_command(name='unlink', description='Unlink from Open World')
    @commands.has_permissions(kick_members=True)
    async def openworldunlink(self, ctx: commands.Context):
        guild = ctx.guild
        channel = ctx.channel

        connection = self.init.get_connection(channel.id, guild.id)
        
        if not connection:
            await ctx.send(
                embed=discord.Embed(
                    description=":no_entry: **Your channel is not registered for Open World Chat**",
                    color= 0xFF0000)
                    )
            
        curr_channel = self.bot.get_channel(connection['channel_id'])

        if curr_channel:
            webhooks = await curr_channel.webhooks()

            for webhook in webhooks:
                if webhook.url == connection['webhook']:
                    await webhook.delete()
                    break

        # Removing the connection in the database
        await self.repos.guild_repository.delete(connection)
        self.init.connection.remove(connection)
        await ctx.send(
            embed=discord.Embed(
                description=":white_check_mark: **Unlinked from Open World Chat**",
                color= 0x00FF00)
            )   
    
    #Get Current Lobby
    @commands.hybrid_command(name='current', description='Current Lobby description')
    async def current_lobby(self, ctx: commands.Context):

        # find the lobby in the database
        guild = ctx.guild
        channel = ctx.channel

        # Validate connection
        connection = self.init.get_connection(channel.id, guild.id)
        
        if not connection:
            await ctx.send(
                embed=Embed(
                    title=":no_entry: This channel is not connected to any channel",
                    color=0xFF0000
                )
            )
        
        data = self.init.get_lobby_basic_data(connection['lobby_id'])
             
        if not data:
            await ctx.send(embed=Embed(description="Something went wrong on searching your connection", color=0xFF0000))
        
        guild_data  = await self.bot.fetch_guild(data['guild_id'])

        embed = discord.Embed(
            title= data['title'], 
            color=0xFFC0CB
        )
        
        embed.set_thumbnail(url=str(guild_data.icon.url))
        embed.add_field(name="Host", value=f"**Name:** {guild_data.name} \n**Members:** {guild_data.approximate_member_count}", inline=True)
        embed.add_field(
            name="Info", 
            value= f"Connections: `{self.init.get_lobby_length(data['lobby_id'])}/{data['limit']}` \n"
                    f" Lobby code: {data['lobby_id']}",
            inline=True)
                
        topics = ""
        for topic in data["topics"]:
            topics += f"`{topic}` "

        embed.add_field(name="Topics", value=topics, inline=False)

        embed.add_field(name="Description", value=data['description'], inline=False)


        connections = self.init.get_lobby_connections(data['lobby_id'])
        format = ""
        limit = 1
        for conn in connections:
            if limit > 10:
                break
            else:
                format += f"{conn["guild_name"]}\n"
                limit += 1

        embed.add_field(name="Connections", value=format, inline=False)
        embed.set_footer(text=data['footer_message'])
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='switch', description='Switch to a different server lobby')
    @commands.has_permissions(kick_members=True)
    async def switch_lobby(self, ctx: commands.Context, lobby_id : str = None):

        # Prepare varaibles to be use        
        guild = ctx.guild
        channel = ctx.channel

        # Verify connection
        connection = self.init.get_connection(channel.id, guild.id)

        if not connection:
            await ctx.send(
                embed=discord.Embed(
                    description=":no_entry: **Your channel is not registered for Open World Chat**",
                    color= 0xFF0000)
                    )

        # Get lobby data
        lobby_data = self.init.get_lobby_basic_data(connection['lobby_id'])

        if not lobby_data:
            await ctx.send(
                embed=discord.Embed(
                    description="Something whent wrong on fetching lobby data",
                    color= 0xFF0000)
                    )
            
        if lobby_id:
           # If provided create data for connection
            lobby_data = self.init.isLobbyExists(lobby_id)

            if not lobby_data:
                embed = Embed(
                    title="The lobby ID that you have provided is not available",
                    color=0xFF0000  # Red color
                    )
                await ctx.send(embed=embed)
                return 
            # Get Lobby Config for details such as limit
            data = self.init.get_lobby_basic_data(lobby_id)

            # Check the limit
            current = self.init.get_lobby_length(lobby_id)

            if current >= data['limit']:
                embed = Embed(
                    title="Lobby is full",
                    color=0xFF0000  # Red color
                )
                await ctx.send(embed=embed)
                return
        else:
            # provide a list
            available_lobbies = self.init.get_all_lobby_data()
            
            views = LobbyPagination(
                data = available_lobbies,
                title = "Switch Lobbies",
                author= ctx.message.author,
                addional_info_field= False,
                add_dropdown= True,
                drop_placeholder= "Select lobby"
            )
            await views.send(ctx)

            try:
                await asyncio.wait_for(views.wait(), timeout=60)
            except asyncio.TimeoutError:
                await views.message.edit(view=None)
            
            selected_val = views.value
            
            if selected_val == "Back":
                await views.message.edit(view=None)
                return

            if selected_val == connection['lobby_id']:
                embed = Embed(
                    title="You cannot switch to same lobby",
                    color=0xFF0000  # Red color
                    )
                await ctx.send(embed=embed)
                return
                        
            data = self.init.get_lobby_basic_data(selected_val)

            current = self.init.get_lobby_length(data['lobby_id'])

            if current >= data['limit']:
                embed = Embed(
                    title=":no_entry: Lobby is full",
                    color=0xFF0000  # Red color
                )
                await ctx.send(embed=embed)
                return
         # Delete the current connection
            
        await self.repos.guild_repository.delete(connection)
        self.init.connection.remove(connection)

        # Create new connection        
        connection_data = {
            "lobby_id": data['lobby_id'],
            "channel_id": channel.id,
            "webhook": connection['webhook'],
            "guild_id": guild.id,
            "guild_name": guild.name
        }

        res = await self.repos.guild_repository.create(connection_data)
        connection_data['_id'] =res.inserted_id
        self.init.connection.append(connection_data)

        embed = Embed(
            description=f":white_check_mark: **You have switched to {data['title']}**",
            color=0x7289DA 
        )

        await ctx.send(embed=embed)
        await self.on_join_announce(ctx, connection_data['lobby_id'])     

    # TODO: This is a mod command inside globalchat command
    @commands.hybrid_command(name="report",description="Report a user for misbehaving, and attach a picture for proff")
    async def report_user(self, ctx, username, reason, attacment:discord.Attachment = None):
        
        await ctx.send(embed=discord.Embed(description=f"User has been reported"))
        await self.init.log_report_by_user(username,ctx.author.name,reason,attacment)

    async def on_join_announce(self, ctx: commands.Context, lobby_id: str):
        async with aiohttp.ClientSession() as session:
            tasks = []

            for document in self.init.connection:
                    if document["channel_id"] != ctx.message.channel.id and lobby_id == str(document["lobby_id"]):
                        webhook = Webhook.from_url(document["webhook"], session=session)
                        embed = Embed(color= 0xEB459F)
                        embed.set_author(name=f"{ctx.guild.name} has joined the chat",icon_url=ctx.guild.icon.url)

                        tasks.append(
                            webhook.send(
                                avatar_url= self.bot.user.avatar.url,
                                username=self.bot.user.name,
                                embed=embed,
                                wait=True  
                            )
                        )

            await asyncio.gather(*tasks)
                        

## View
class LobbyDropDown(discord.ui.Select):
    def __init__(self,server_lobbies,author, on_item_added):
        self.server_lobbies = server_lobbies
        self.author = author
        self.on_item_added = on_item_added
        
        options = [discord.SelectOption(label=lobby["lobbyname"], value=lobby["lobbyname"]) for lobby in self.server_lobbies]
        super().__init__(
            placeholder="Select a lobby",
            options=options,
            min_values=1,
            max_values=1
        )
    async def callback(self, interaction):
        if interaction.user == self.author:
            await interaction.response.defer()
            await self.on_item_added(interaction.data['values'][0])
                 
class ConnectDropDown(discord.ui.View):
    def __init__(self, author, server_lobbies):
        super().__init__()
        self.lobby = None
        self.add_item(LobbyDropDown(server_lobbies,author, self.on_item_added))

    async def on_item_added(self,value):
        self.lobby = value
        self.stop()

class DynamicChoice(discord.ui.View):
    def __init__(self, author, choices):
        super().__init__()
        self.author = author
        self.value = None
        
        # Dynamically create buttons based on the provided choices
        for choice in choices:
            self.add_item(self.create_button(choice))
    
    def create_button(self, label):
        # Create a button with the given label
        button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
        button.callback = self.button_callback
        return button

    async def button_callback(self, interaction: discord.Interaction):
        if interaction.user == self.author:
            # Find the button that was clicked by matching custom_id
            for x in interaction.message.components:
                for button in x.children:
                    if button.custom_id == interaction.data['custom_id']:
                        self.value = button.label
            await interaction.response.defer()
            self.stop()
