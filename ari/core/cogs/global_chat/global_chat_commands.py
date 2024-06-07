import asyncio
import aiohttp
import discord
from discord.ext import commands
from discord import Embed, Webhook

class Global(commands.Cog):
    def __init__(self, bot : commands.Bot, initialization, repositories):
        self.bot = bot
        self.init = initialization
        self.repos = repositories


    # TODO: Improve Connect
    @commands.hybrid_command(name='connect', description='Link to Open World')
    async def openworldlink(self, ctx, channel: discord.TextChannel):

        # ======================================================================================
        async def Validation(guild_id,channel_id):
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
                return {'message':'Failed', 'message_data':sent_message, 'server_name':None}
            else:
                return {'message':'Success', 'message_data':sent_message, 'server_name':existing_guild}
        
        async def SelectLobbies(guild_id,sent_message):
            # Getting lobbies and selecting available lobbies
            # ======================================================================================
            # Issue: handle the issue of user selecting the full lobbies
            # ======================================================================================
            async def SelectLobby():
                message = await self.show_lobbies_embed(ctx,"Available Lobbies", description=None)
                lobby =ConnectDropDown(ctx.message.author,self.init.server_lobbies)
                
                message_drp = await ctx.send(view=lobby)
                try:
                    await asyncio.wait_for(lobby.wait(), timeout=60)
                except asyncio.TimeoutError:
                    await ctx.send("You didn't respond within the specified time.")
                    await message.delete()
                    await message_drp.delete()
                    raise Exception("")
                
                await message.delete()
                await message_drp.delete()
                return lobby.lobby

            async def AboutLobby(about):
                for lobby in self.init.server_lobbies:
                    if lobby["lobbyname"] == about:
                        description = lobby["description"]
                # This is a duplicate from current_lobby command
                guilds = self.init.getAllGuildUnderLobby(about)
                data = ""
                x = 1
                if guilds:
                    for guild in guilds:
                        text = f"**{x}**) **{guild['server_name']}**"
                        data += text + "\n\n"
                        x += 1
                else:
                    data = "There's no guild connected to this lobby"
                choice = Choice(ctx.message.author)

                embed = Embed(
                    title= about,
                    description=description,
                    color=0x7289DA
                )

                
                embed.add_field(name="Guilds",value=data)
                await sent_message.edit(embed = embed)
                msg_choice = await ctx.send(view=choice)
                
                try:
                    await asyncio.wait_for(choice.wait(), timeout=60)
                except asyncio.TimeoutError:
                    await ctx.send("You didn't respond within the specified time.")
                    await msg_choice.delete()
                    await sent_message.delete()
                    raise Exception("")
                
                await msg_choice.delete()
                return choice.value
            
            # ======================================================================================
            # Menu Manager
            
            while True:
                lobby = await SelectLobby()
                choice = await AboutLobby(lobby)
               
                if choice is True:
                    return {'message':'Success', 'message_data':sent_message, 'lobby': lobby} 
        async def CheckLobby(sent_message, lobby):
            message = "Full"

            lobbyData = await self.init.getAllLobby()
            
            limit = None  
            for data in self.init.server_lobbies:
                
                if data["lobbyname"] == lobby:
                    limit = data.get("limit")  # Use .get() to avoid KeyError if "limit" is not present
                    break
            
            if limit is not None:  # Proceed only if limit is found
                for x in lobbyData:
                    if x.get("name") == lobby and x.get("connection", 0) < limit:  # Adjust condition check
                        message = "Available"
                        break

            return {'message': message, 'message_data':sent_message} 
        
        async def Login(guild_id, sent_message):  
            # Logging in process
            embed = Embed(
                description="Logging in ...",
                color=0x7289DA 
            )
            await sent_message.edit(embed=embed)
            await asyncio.sleep(1)
            embed.description = "Linking into Open World Server..."
            await sent_message.edit(embed=embed)
            await asyncio.sleep(1)
            embed.description = f"Confirming Connection with World - `{guild_id}`..."
            await sent_message.edit(embed=embed)
            await asyncio.sleep(1)
            embed.description = f"Fetching Data from World - `{guild_id}`..."
            await sent_message.edit(embed=embed)
            await asyncio.sleep(1)

            return {'message':'Success', 'message_data':sent_message} 
        
        async def CreateConnection(lobby, sent_message, guild_name):
            # Create Connection
            # now connect
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
            return {'message':'Success', 'message_data':sent_message} 
        
        def isFailed(response):
            if(response['message'] == "Failed"):
                raise Exception("")
            else:
                return response
            
        async def Sequence(guild_id, channel_id, guild_name):
            
            while True:
                response = isFailed(await Validation(guild_id, channel_id))
   
                responseWithlobby = isFailed(await SelectLobbies(guild_id, response['message_data']))

                response = isFailed(await CheckLobby(response['message_data'], responseWithlobby["lobby"]))
                if response["message"] == "Available":
                    break
            response = isFailed(await Login(guild_id, responseWithlobby['message_data']))
            
            response = isFailed(await CreateConnection(responseWithlobby['lobby'], response['message_data'], guild_name))
            await self.on_join_announce(ctx,guild_name, responseWithlobby['lobby'])

        # ======================================================================================
        # Runtime Manager

        guild_id = ctx.guild.id
        channel_id = channel.id
        guild_name = ctx.guild.name

        # Sequence 
        await Sequence(guild_id, channel_id, guild_name)

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
    
    async def on_join_announce(self, ctx, guild_name, lobbyname):
        async with aiohttp.ClientSession() as session:
            tasks = []

            for document in self.init.guild_data:
                channels = document["channels"]
                for channel in channels:
                    if channel["channel_id"] != ctx.message.channel.id and lobbyname == channel["lobby_name"]:
                        webhook = Webhook.from_url(channel["webhook"], session=session)
                        embed = Embed(description=f"**{guild_name}** has joined the chat", color= 0xEB459F)
                        
                        tasks.append(
                            webhook.send(
                                avatar_url= self.bot.user.avatar.url,
                                username=self.bot.user.name,
                                embed=embed,
                                wait=True  
                            )
                        )

            await asyncio.gather(*tasks)
                        
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
        await self.show_lobbies_embed(ctx, title="Lobbies Online",description="Some description to add")

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
        return await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='switch', description='Switch to a different server lobby')
    @commands.has_permissions(kick_members=True)
    async def switch_lobby(self, ctx):

        async def Menu():
            async def ConfirmLeave():
                embed = Embed(
                    description= ":warning: **Are you sure do you want to leave?**",
                    color = 0x7289DA 
                )
                message = await ctx.send(embed=embed)
                
                choice = Choice(ctx.message.author)
                msg_choice = await ctx.send(view=choice)

                try:
                    await asyncio.wait_for(choice.wait(), timeout=60)
                except asyncio.TimeoutError:
                    await ctx.send("You didn't respond within the specified time.")
                    await msg_choice.delete()
                    await message.delete()
                    raise Exception("")
                
                await message.delete()
                await msg_choice.delete()
                return choice.value
            
            async def SelectLobby():
                message = await self.show_lobbies_embed(ctx,"Available Lobbies", description=None)
                lobby = ConnectDropDown(ctx.message.author,self.init.server_lobbies)
                message_drop = await ctx.send(view=lobby)
                try:
                    await asyncio.wait_for(lobby.wait(), timeout=60)
                except asyncio.TimeoutError:
                    await ctx.send("You didn't respond within the specified time.")
                    await message_drop.delete()
                    await message.delete()
                    raise Exception("")
                

                await message_drop.delete()
                return {"lobby": lobby.lobby, "message":message}
            # ======================================================================================
            # Menu Manager

            while True:
                choice = await ConfirmLeave()
                if choice == False:
                    return {'message': 'Failed', 'message_data': None, "lobby": None}
                response = await SelectLobby()
                
                if response['lobby']:
                    return {'message': 'Success', 'message_data': response["message"], "lobby":  response['lobby']}



        async def Validation(guild_id,channel_id):

            existing_guild = self.init.find_guild(guild_id, channel_id)

            if existing_guild:
                channels = existing_guild.get("channels",[])
                for channel in channels:
                    # Checks if user is in the lobby

                    if channel['channel_id'] == channel_id:
                        return {'message': 'Success' , 'channel': channel}
            else:
                embed = Embed( 
                    description=f":no_entry: **Your channel is not registered for Open World Chat**",
                    color=0x7289DA 
                )
                await ctx.send(embed=embed)
                return {'message': 'Failed', 'channel': None }
            
        # Might change this to a drop down function
        async def updateLobbyConnection(guild_id, channel_id, message, lobby):
            
            await self.repos.update_guild_lobby(guild_id, channel_id, lobby)

            embed = Embed(
                description=f":white_check_mark: **You have switched to {lobby}**",
                color=0x7289DA 
            )

            await message.edit(embed=embed)

        def isFailed(response):
            if(response['message'] == "Failed"):
                raise Exception("")
            else:
                return response
            
        async def Sequence(guild_id,channel_id):
            
            channel = isFailed(await Validation(guild_id, channel_id))
            
            lobby = isFailed(await Menu())

            if channel['channel']['lobby_name'] == lobby['lobby']:
                await ctx.send(
                    embed = Embed(
                        description= f"<:no:1226959471910191154> **You're already in {lobby["lobby"]}**"
                    )
                )
            else:
                await updateLobbyConnection(guild_id, channel_id, lobby['message_data'] , lobby["lobby"])
        # ======================================================================================
        # Run Time Manager
        # ======================================================================================
        # Potential Issues:
        # - Chat still goes even during switching
        #  
        # ======================================================================================
        
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id

        # Sequence
        await Sequence(guild_id,channel_id)

    @commands.hybrid_command(name="report",description="Report a user for misbehaving, and attach a picture for proff")
    async def report_user(self, ctx,username, reason, attacment:discord.Attachment):
        if not attacment:
            await ctx.send(embed=discord.Embed(description=f"Please provide a picture"))

        await ctx.send(embed=discord.Embed(description=f"User has been reported"))
        await self.init.log_report_by_user(username,ctx.author.name,reason,attacment)


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
class Choice(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.value = None

    @discord.ui.button(label="Yes" , style=discord.ButtonStyle.green)
    async def btn1(self, interaction: discord.interactions, btn:discord.ui.button):
        if interaction.user == self.author:
            self.value = True
            await interaction.response.defer()
            self.stop()

    @discord.ui.button(label="Back" , style=discord.ButtonStyle.red)
    async def btn2(self, interaction: discord.interactions, btn:discord.ui.button):
        if interaction.user == self.author:
            self.value = False
            await interaction.response.defer()
            self.stop()
