import asyncio
import logging
import aiohttp
import discord
from discord.ext import commands
from discord import Embed, Webhook


log = logging.getLogger("globalchat.commands")

class Global(commands.Cog):
    def __init__(self, bot : commands.Bot, initialization, repositories):
        self.bot = bot
        self.init = initialization
        self.repos = repositories


    # TODO: Improve Connect
    @commands.hybrid_command(name='connect', description='Link to Open World')
    async def openworldlink(self, ctx, channel: discord.TextChannel):
        
        guild_id = ctx.guild.id
        channel_id = channel.id
        guild_name = ctx.guild.name

        embed = Embed(
            description="Preparing ...",
            color=0x7289DA 
        )
        sent_message = await ctx.send(embed=embed)
        existing_guild = self.init.find_guild(guild_id, channel_id)
        if existing_guild:
            embed = Embed(
                title=":no_entry: Your channel is already registered for Open World Chat",
                description="Type `a!unlink` to unlink your Open World\n*This will only unlink from the Open World channel*",
                color=0xFF0000  # Red color
            )
            await sent_message.edit(embed=embed)
            return 

        # TODO: Auto Connect Feature
        # Shows an embed that asks the user to proceed or explore more
        #=====================================
        lobby = await self.handle_auto_connect(ctx)
        
        lobby = await self.handle_lobby_selection(ctx)
        if not lobby:
            return
        
        # Logging in process
        steps = [
            "Logging in ...",
            "Linking into Open World Server...",
            f"Confirming Connection with World - `{guild_id}`...",
            f"Fetching Data from World - `{guild_id}`..."
        ]
        
        for step in steps:
            embed.description = step
            await sent_message.edit(embed=embed)
            await asyncio.sleep(1)
        

        await self.repos.create_guild_document(guild_id, channel, guild_name, lobby)
        embed = Embed(
            description=f':white_check_mark: **LINK START!! You are now connected to {lobby}**',
            color=0x7289DA 
        )
        await sent_message.edit(embed=embed)
        await asyncio.sleep(1)
        # sends a successful message
        embed = Embed(
            title="Thank you for linking with Open World Server!",
            description= self.init.openworldThanksMessage,
            color=0x00FF00 
        )

        message = await ctx.send(embed=embed)

        await message.add_reaction('✅')

        await self.on_join_announce(ctx,guild_name, lobby)
       
    async def handle_auto_connect(self,ctx):
        pass

    async def handle_lobby_selection(self,ctx):
       
        while True:
        
            embed = await self.show_lobbies_embed(ctx,"Available Lobbies", description=None)
            lobby =ConnectDropDown(ctx.message.author,self.init.server_lobbies)
            
            message_drp = await ctx.send(view=lobby,embed=embed)
            try:
                await asyncio.wait_for(lobby.wait(), timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("You didn't respond within the specified time.")
                await message_drp.delete()
                return
            
            selected_lobby = lobby.lobby
            await message_drp.delete()
        

            for lobby in self.init.server_lobbies:
                if lobby["lobbyname"] == selected_lobby:
                    description = lobby["description"]
                    
            description = next((lobby["description"] for lobby in self.init.server_lobbies if lobby["lobbyname"] == selected_lobby), "No description available")
            guilds = self.init.getAllGuildUnderLobby(selected_lobby)

            data = "\n\n".join([f"**{i+1}**) **{guild['server_name']}**" for i, guild in enumerate(guilds)]) or "There's no guild connected to this lobby"
            choice_view = DynamicChoice(ctx.message.author, ["Confirm","Cancel"])

            embed = Embed(
                title= selected_lobby,
                description=description,
                color=0x7289DA
            )

            
            embed.add_field(name="Guilds",value=data)
            select_lobby_embed = await ctx.send(embed = embed, view=choice_view)
            
            try:
                await asyncio.wait_for(choice_view.wait(), timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("You didn't respond within the specified time.")
                await select_lobby_embed.delete()
                return
                        
            await select_lobby_embed.delete()

            if choice_view.value != "Confirm":
                continue    
        
            lobbyData = await self.init.getAllLobby()
            
            # Validate the lobby limit
            limit = None  
            for data in self.init.server_lobbies:
                if data["lobbyname"] == selected_lobby:
                    limit = data.get("limit") 
                    break

            available = False
            if limit is not None:
                for x in lobbyData:
                    if x.get("name") == selected_lobby and x.get("connection", 0) < limit:  # Adjust condition check
                        available = True
                        break

            if available:
                return selected_lobby  
            else:
                embed = Embed(
                    title= "",
                    description=f"The {selected_lobby} is currently full, choose another lobby to connect.",
                    color=0x7289DA
                )
                await ctx.send(embed = embed)
        

    @commands.hybrid_command(name='unlink', description='Unlink from Open World')
    async def openworldunlink(self, ctx):
        # Initialize needed data
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        
        # checks if the channel exists in the database
        existing_guild = self.init.find_guild(guild_id, channel_id)
        if existing_guild:
            # if it does exists, delete it from database
            await self.repos.delete_guild_document(guild_id, channel_id)
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
    async def current_lobby(self, ctx):
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id

        guild_document = self.init.find_guild(guild_id,channel_id)

        if self.init.server_lobbies:
            if guild_document:

                lobby = guild_document.get("channels",[])
            
                for channel in lobby:
                    if channel["channel_id"] == channel_id:
                        lobby_name = channel['lobby_name']
                        limit = self.init.get_limit_server_lobby(lobby_name)
                        description = None
                        guilds =  self.init.getAllGuildUnderLobby(channel['lobby_name'])
                        connection = self.init.get_lobby_count(channel['lobby_name'])
                        # Lobby Data
                        for lobby in self.init.server_lobbies:
                            if lobby["lobbyname"] == lobby_name:
                                description = lobby["description"]
                        data = ""
                        x = 1

                        if guilds:
                            for guild in guilds:
                                
                                text = f"**{x}**) **{guild['server_name']}**"
                                data += text + "\n\n"
                                x += 1
                        else:
                            data = "There's no guild connected to this lobby"

                        embed = Embed(
                            title= f"{channel['lobby_name']} - {connection}/{limit}",
                            description= description,
                            color= 0xFFC0CB 
                        )
                        embed.add_field(name="Connected:", value = data)
                        return await ctx.send(embed=embed)
            else:
                embed = Embed(
                    description=f":no_entry: **Your channel is not registered for Open World Chat**",
                    color=0xFFC0CB
                )
                
                return await ctx.send(embed=embed)

    @commands.hybrid_command(name='lobbies', description='Current Lobby description')
    async def show_lobbies(self, ctx):
        embed = await self.show_lobbies_embed(ctx, title="Lobbies Online",description="Some description to add")

        await ctx.send(embed = embed)

    async def show_lobbies_embed(self, ctx, title ,description):
        lobby_data = await self.init.getAllLobby()
        formatted_data = ""

        for data in lobby_data:
            limit = self.init.get_limit_server_lobby(data["name"])
            connection = data['connection']
            
            if connection > limit - 5:
                # If the number of connections is close to the limit, display 🔴
                text = f"\n🔴 **{data['name']}**\n {connection}/{limit} guilds connected"
            elif connection > limit - 10:
                # If the number of connections is moderate, display 🟠
                text = f"\n🟠 **{data['name']}**\n {connection}/{limit} guilds connected"
            else:
                # If the number of connections is low, display 🟢
                text = f"\n🟢 **{data['name']}**\n {connection}/{limit} guilds connected"
            
            formatted_data += text + "\n"

        embed = Embed(
            title= title,
            description= description,
            color=0x7289DA 
        )
        embed.add_field(name="Public Lobbies",value=formatted_data)
        return embed
    
    @commands.hybrid_command(name='switch', description='Switch to a different server lobby')
    async def switch_lobby(self, ctx):
        
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id

        # Validation
        existing_guild = self.init.find_guild(guild_id, channel_id)
        
        if not existing_guild:
            embed = Embed( 
                description=f":no_entry: **Your channel is not registered for Open World Chat**",
                color=0x7289DA 
            )  
            await ctx.send(embed=embed)
            return
        
        for channel in existing_guild["channels"]:
            if channel["channel_id"] == channel_id:
                connection_data = channel

        # Confirmation
        embed = Embed(
            description= ":warning: **Are you sure do you want to leave?**",
            color = 0x7289DA 
        )
        choice = DynamicChoice(ctx.message.author, ["Confirm","Cancel"])
        confirm_message = await ctx.send(embed=embed,view=choice)

        try:
            await asyncio.wait_for(choice.wait(), timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("You didn't respond within the specified time.")
            await confirm_message.delete()
            raise Exception("")
        
        await confirm_message.delete()

        if choice.value == "Cancel":
            return
        
        # Switching Process
        while True:
            embed = await self.show_lobbies_embed(ctx,"Available Lobbies", description=None)
            lobby = ConnectDropDown(ctx.message.author, self.init.server_lobbies)
            message_drop = await ctx.send(embed=embed,view=lobby)

            try:
                await asyncio.wait_for(lobby.wait(), timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("You didn't respond within the specified time.")
                await message_drop.delete()
                raise Exception("")
            
            await message_drop.delete()
            selected_lobby = lobby.lobby
            if connection_data["lobby_name"] == selected_lobby:
                    await ctx.send(
                        embed = Embed(
                            description= f"<:no:1226959471910191154> **You're already in {selected_lobby}**"
                        )
                    )
            else:
                break

        await self.repos.update_guild_lobby(guild_id, channel_id, selected_lobby)

        embed = Embed(
            description=f":white_check_mark: **You have switched to {selected_lobby}**",
            color=0x7289DA 
        )

        await ctx.send(embed=embed)
        await self.on_join_announce(ctx, ctx.guild.name, selected_lobby)
       
              

    @commands.hybrid_command(name="report",description="Report a user for misbehaving, and attach a picture for proff")
    async def report_user(self, ctx,username, reason, attacment:discord.Attachment):
        if not attacment:
            await ctx.send(embed=discord.Embed(description=f"Please provide a picture"))

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
