import asyncio
import logging
import aiohttp
import discord
from discord.ext import commands
from discord import Embed, Webhook

import discord.ext
import discord.ext.commands
from .global_chat_ui_views import CreateLobbyModal, LobbyPagination
from .global_chat_initialization import Intialization
log = logging.getLogger("globalchat.commands")

class Global(commands.Cog):
    def __init__(self, bot : commands.Bot, initialization : Intialization, repositories):
        self.bot = bot
        self.init = initialization
        self.repos = repositories

    # Conditions: Perms to kick user
    @commands.hybrid_command(name='createlobby',with_app_command=True, description='1 lobby per server, Users need to have kick permissions to use this command')
    @commands.has_permissions(kick_members=True)
    async def createLobby(self, ctx:commands.Context):
        
        guild_id = ctx.guild.id
        canCreate = False
        
        log.info(self.init.lobby_data)
        for id in self.init.lobby_data:
            if guild_id == id["guild_id"]:
                canCreate = True
            
        if not canCreate:               
            modal = CreateLobbyModal(self.init.lobby_data)
            response = await ctx.interaction.response.send_modal(modal) 
        else:
            await ctx.send(embed=discord.Embed( description= ":no_entry: You have reached the limit of 1 lobby per server",  color=0xFFC0CB))

    # Making this dynamic and able to edit the website
    @commands.hybrid_command(name='lobby_show', description="Shows more information of the lobby using the code")
    async def showlobbyData(self, ctx: commands.Context, lobby_id: str):

        found = None
        for id in self.init.lobby_data:
            if lobby_id == id['lobby_id']:
                found = id
                break
        
        owner: discord.User = await discord.Client.fetch_user(self.bot, found['owner_id'])
        if not found:
            await ctx.send(embed=Embed(description="Lobby not found",  color=0xFFC0CB))

        topics = ""
        for data in  found["topics"]:
            topics += f"`{data}` "

        embed = discord.Embed(
            title= found['title'], 
            description="> **Connections:** `1/20` \n"
                        f"> **Lobby code:** {found['lobby_id']}",
            color=0xFFC0CB
        )

        embed.add_field(name="Topics", value=topics, inline=False)
        embed.add_field(name="Description", value=found['description'], inline=False)
        embed.set_footer(text=f"Placeholder text",icon_url=owner.avatar.url)
        
        await ctx.send(embed=embed)
    
    
    @commands.hybrid_command(name='connect', description='Link to Open World')
    @commands.has_permissions(kick_members=True)
    async def openworldlink(self, ctx : commands.Context, lobby_id: str = None):
        
        # Validate Users
        guild = ctx.guild
        channel = ctx.channel

        existing_guild = None
        for con in self.init.connection:
            if(con['channel_id'] == channel.id and con['guild_id'] == guild.id):
                existing_guild = con

        if existing_guild:
            embed = Embed(
                title=":no_entry: Your channel is already registered for Open World Chat",
                description="Type `a!unlink` to unlink your Open World\n*This will only unlink from the Open World channel*",
                color=0xFF0000  # Red color
            )
            await ctx.send(embed=embed)
            return 
        
        # Validate if lobby_id is provided
        if lobby_id:
            isValid = await self.validateLobby(lobby_id)

            if not isValid:
                embed = Embed(
                    title=":no_entry: The lobby ID that you have provided is not available",
                    color=0xFF0000  # Red color
                    )
                await ctx.send(embed=embed)
                return 
            # else if the lobby id is not provided then we'll do the auto connect feature
        else:
            # TODO: Implement a auto connect feautre
            isValid = await self.validateLobby(self.init.generalLobby)
            # This should always be true

        # Connect it

       
        webhook = await channel.create_webhook(name=isValid['title'])
        data = {
            "lobby_id": lobby_id,
             "channel_id": channel.id,
             "webhook": webhook.url,
             "guild_id": guild.id,
             "guild_name": guild.name
        }
        res = await self.repos.guild_repository.create(data)
        data['_id'] =res.inserted_id
        
        self.init.connection.append(data)

        # Send a success message if its successfull
        embed = Embed(
            description=f':white_check_mark: **LINK START!! You are now connected to {isValid['title']}**',
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

        # TODO: Update this soon
        # await self.on_join_announce(ctx,guild_name, lobby)
       
    async def validateLobby(self, selected_lobby):
        for lobby in self.init.lobby_data:
            if selected_lobby == lobby['lobby_id']:
                return lobby
        return None
        
    @commands.hybrid_command(name='unlink', description='Unlink from Open World')
    @commands.has_permissions(kick_members=True)
    async def openworldunlink(self, ctx: commands.Context):
        guild = ctx.guild
        channel = ctx.channel

        existing_guild = None
        for con in self.init.connection:
            if con['guild_id'] == guild.id and con['channel_id'] == channel.id:
                existing_guild = con
        
        if existing_guild:
            # if it does exists, delete it from database
            await self.repos.guild_repository.delete(existing_guild)
            self.init.connection.remove(existing_guild)
            await ctx.send(
                embed=discord.Embed(
                    description=":white_check_mark: **Unlinked from Open World Chat**",
                    color= 0x00FF00)
                )
        else:
            # else if doesnt 
            await ctx.send(
                embed=discord.Embed(
                    description=":no_entry: **Your channel is not registered for Open World Chat**",
                    color= 0xFF0000)
                    )
    
    #Get Current Lobby
    @commands.hybrid_command(name='current', description='Current Lobby description')
    async def current_lobby(self, ctx: commands.Context):

        # find the lobby in the database
        guild = ctx.guild
        channel = ctx.channel

        # Determine if connected
        connection = None
        for con in self.init.connection:
            if(con['channel_id'] == channel.id and con['guild_id'] == guild.id):
                connection = con
                break
        
        if not connection:
            await ctx.send(
                embed=Embed(
                    title=":no_entry: This channel is not connected to any channel",
                    color=0xFF0000
                )
            )
        
        # Finding the lobby
        guild_document = None
        for lobby in self.init.lobby_data:
            if lobby['lobby_id'] == connection['lobby_id']:
                guild_document = lobby
                break
       
        if guild_document:
            # If found show data
            topics = ""
            for data in guild_document["topics"]:
                topics += f"`{data}` "

            embed = discord.Embed(
                title= guild_document['title'], 
                description=f"> **Connections:** `{self.init.get_lobby_length(guild_document['lobby_id'])}/{guild_document['limit']}` \n"
                            f"> **Lobby code:** {guild_document['lobby_id']}",
                color=0xFFC0CB
            )

            embed.add_field(name="Topics", value=topics, inline=False)
            embed.add_field(name="Description", value=guild_document['description'], inline=False)
            embed.set_footer(text=f"Placeholder text",icon_url=ctx.author.avatar.url)
            
            await ctx.send(embed=embed)
        else:

            embed = Embed(
                description=f":no_entry: **Your channel is not registered for Open World Chat**",
                color=0xFFC0CB
            )
            
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='lobbies', description='Current Lobby description')
    async def show_lobbies(self, ctx: commands.Context):

        view = LobbyPagination(self.init.lobby_data, current_page=1, sep=5, timeout=None)
        await view.send(ctx)

    @commands.hybrid_command(name='switch', description='Switch to a different server lobby')
    @commands.has_permissions(kick_members=True)
    async def switch_lobby(self, ctx: commands.Context, lobby_id : str):
        
        # Validate
        guild = ctx.guild
        channel = ctx.channel

        # Get the connection
        connection = None
        for con in self.init.connection:
            if con['channel_id'] == channel.id and con['guild_id'] == guild.id:
                connection= con
                break

        lobby_document = None
        for lobby in self.init.lobby_data:
            if lobby['lobby_id'] == connection['lobby_id']:
                lobby_document = lobby
                break

        # Validation for lobby_id
        lobby_exist = None
        for lobby in self.init.lobby_data:
            if lobby['lobby_id'] == lobby_id:
                lobby_exist = lobby

        # Check if the id is provided 
        if connection and lobby_exist:

            # Delete the current connection
            await self.repos.guild_repository.delete(connection)
            self.init.connection.remove(connection)

            # Create new connection
            webhook = await channel.create_webhook(name=lobby_document['title'])
            
            data = {
                "lobby_id": lobby_id,
                "channel_id": channel.id,
                "webhook": webhook.url,
                "guild_id": guild.id,
                "guild_name": guild.name
            }

            res = await self.repos.guild_repository.create(data)
            data['_id'] =res.inserted_id
            self.init.connection.append(data)

            embed = Embed(
                description=f":white_check_mark: **You have switched to {lobby_exist['title']}**",
                color=0x7289DA 
            )
        else:
            embed = Embed( 
                description=f":no_entry: **Your channel is not registered for Open World Chat**",
                color=0x7289DA 
            )
            await ctx.send(embed=embed)
            return
        
        await ctx.send(embed=embed)
        # await self.on_join_announce(ctx, ctx.guild.name, lobby)
       
       
              

    @commands.hybrid_command(name="report",description="Report a user for misbehaving, and attach a picture for proff")
    async def report_user(self, ctx, username, reason, attacment:discord.Attachment = None):
        
        await ctx.send(embed=discord.Embed(description=f"User has been reported"))
        await self.init.log_report_by_user(username,ctx.author.name,reason,attacment)

    async def on_join_announce(self, ctx, guild_name, lobbyname):
        async with aiohttp.ClientSession() as session:
            tasks = []

            for document in self.init.guild_data:
                channels = document["channels"]
                for channel in channels:
                    if channel["channel_id"] != ctx.message.channel.id and lobbyname == channel["lobby_name"]:
                        webhook = Webhook.from_url(channel["webhook"], session=session)
                        embed = Embed(color= 0xEB459F)
                        embed.set_author(name=f"{guild_name} has joined the chat",icon_url=ctx.guild.icon.url)

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
