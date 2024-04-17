import asyncio
import discord, typing
from discord.ext import commands
from discord import app_commands

class GlobalChatMod(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.controlChannel = 1230160106369318965
        
    async def cog_load(self):
        self.openworld_cog = self.bot.get_cog("OpenWorldServer")
        self.server_lobbies = self.openworld_cog.server_lobbies
        self.muted_users = self.openworld_cog.muted_users
        self.malicious_urls = self.openworld_cog.malicious_urls
        self.malicious_words = self.openworld_cog.malicious_words
        print("Add Data in Global chat is reloaded")
        
    @commands.hybrid_command(name="report",description="Report a user for misbehaving, and attach a picture for proff")
    async def report_user(self, ctx,username, reason, attacment:discord.Attachment):
        if not attacment:
            await ctx.send(embed=discord.Embed(description=f"Please provide a picture"))

        await ctx.send(embed=discord.Embed(description=f"User has been reported"))
        await self.log_report(username,ctx.author.name,reason,attacment)

    @commands.command(name="moderation")
    #@commands.has_role("@Ari Global Mod")
    async def GcCommands(self,ctx):
        embed = discord.Embed(
            title="Moderation Commands",
            description= (
                "Commands aren't registered as slash commands for limited visibility"
            ),
            color=0xFFC0CB
        )
        embed.add_field(name="Global Chat Commands", value=(
            "`a!reloaddata` - Reloads data incase data doesnt match / registered\n"
            "`a!listmuted` - Shows all muted users\n"
            "`a!mute <id> \" reason \"` - Mute user globally\n"
            "`a!unmute <id>` - Unmute user\n\n"
            "**Owner Only**\n"
            "`a!add_lobby \"Lobby Name\"` - Add public global chat\n"
            "`a!remove_lobby \"Lobby Name\"` - Remove public chat\n"
            "`a!add_bad_words` \"link\" - Add word to filter\n"
            "`a!add_block_link` \"word\" - Add word to filter\n"
        ), inline=False)
        await ctx.send(embed = embed)
        
    @commands.command(name="listmuted")
    async def getAllMuted(self,ctx):
        format_data = ""
        if self.muted_users:
            x=1
            for data in self.muted_users:
                text = f"{x}) **{data['name']} || {data['id']}**\nReason : {data['reason']}"
                format_data += text + "\n"
                x += 1

        embed = discord.Embed(
            title="Muted List",
            description=format_data
        )
        await ctx.send(embed=embed)

    @commands.command(name='mute')
    #@commands.has_role("@Ari Global Mod")
    async def MuteUser(self, ctx, id : int,reason:str):
        user = await self.bot.fetch_user(id)
        channel = ctx.guild.get_channel(self.controlChannel)
        
        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return
        
        if user.bot or not user:
            await ctx.send(embed=discord.Embed( description=" No User Found"))
            return
        
        data = {
            "id": user.id,
            "name" : user.name,
            "reason": reason,
            "mutedBy" : ctx.message.author.name
        }
        await self.bot.muted_repository.create(data)
        self.muted_users.append(data)
        await ctx.send(embed=discord.Embed( description=f" User {user.id} ({user.name}) has been muted"))

    @commands.command(name='unmute')
    #@commands.has_role("@Ari Global Mod")
    async def UnMuteUser(self, ctx, id: int):
        user = await self.bot.fetch_user(id)
        channel = ctx.guild.get_channel(self.controlChannel)
        exists = await self.bot.muted_repository.findOne(id)

        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return
        
        if user.bot or not user or not exists:
            await ctx.send(embed=discord.Embed( description=" No User Found"))
            return
        
          
        sender = self.bot.get_user(id) 
        await self.bot.muted_repository.delete(user.id)
        self.muted_users.remove(exists)
        await sender.send(embed=discord.Embed(description=f"You have been unmuted from Global Chat!\n\n Welcome back! try to not get reported again"))
        await ctx.send(embed=discord.Embed( description=f" User {user.id} ({user.name}) has been unmuted"))
          
    @commands.hybrid_command(name='add_lobby')
    @commands.is_owner()
    async def AddLobbies(self, ctx, name:str, description: str ,limit:int):
        channel = ctx.guild.get_channel(self.controlChannel)
        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return  
        
        if self.server_lobbies:
            for x in self.server_lobbies:
                if name == x['lobbyname']:
                    await ctx.send(embed=discord.Embed( description="Lobby Exists"))
                    return

        data = {
            "lobbyname":name,
            "description": description,
            "limit":limit
        }
        await self.bot.lobby_repository.create(data)
        self.server_lobbies.append(data)
        await ctx.send(embed=discord.Embed( description=f" Lobby {name} has been newly added"))
    
    # Doesn't Work
    # @commands.hybrid_command(name='remove_lobby')
    # @commands.is_owner()
    # async def RemoveLobbies(self, ctx, name:str):
    #     channel = ctx.guild.get_channel(self.controlChannel)
    #     if ctx.channel.id != self.controlChannel:
    #         await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
    #         return  
    #     lobby = await self.bot.lobby_repository.findOne(name)
    #     print(self.server_lobbies)
    #     if self.server_lobbies and lobby:
    #         for x in self.server_lobbies:
    #             print(x['lobbyname'])
    #             print(lobby['lobbyname'])
    #             print(len(x['lobbyname']))
    #             print(len(lobby['lobbyname']))
    #             if lobby['lobbyname'].strip() == x['lobbyname'].strip():
    #                 await self.bot.lobby_repository.delete(lobby['lobbyname'])
    #                 self.server_lobbies.remove(x)
    #                 return
                                
    #     await ctx.send(embed=discord.Embed( description="Lobby Doesnt Exists"))
    
    @commands.command(name='add_block_link')
    @commands.is_owner()
    async def AddblockLinks(self, ctx, content):
        channel = ctx.guild.get_channel(self.controlChannel)
        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return
        self.malicious_urls.append(content)
        await self.bot.malicious_urls.create(content)
        await ctx.send(embed = discord.Embed(
            description= f"Content has been added to list"
        ))
    
    @commands.command(name='add_bad_words')
    @commands.is_owner()
    async def Addblockwords(self,ctx, content):
        channel = ctx.guild.get_channel(self.controlChannel)
        if ctx.channel.id != self.controlChannel:
            await ctx.send(embed=discord.Embed( description=f" Not the moderation Channel #{channel}"))
            return
        self.malicious_words.append(content)
        await self.bot.malicious_words.create(content)
        await ctx.send(embed = discord.Embed(
            description= f"Content has been added to list"
        ))

    async def log_report(self,name,reportedBy,reason, attachments):
        guild = self.bot.get_guild(939025934483357766)
        target_channel = guild.get_channel(975254983559766086)

        embed = discord.Embed(
            title="Reported",
            description= f"**User {name} has reported by {reportedBy}**"
        )
        embed.set_footer(text = f"reported by {reportedBy}")
        
        if not isinstance(attachments, list):
           attachments = [attachments]

        for index, attachment in enumerate(attachments, start=1):
            embed.add_field(name=f"Proof {index}", value=attachment.url)
        
        await target_channel.send(embed=embed)

        
async def setup(bot:commands.Bot):
    await bot.add_cog(GlobalChatMod(bot))