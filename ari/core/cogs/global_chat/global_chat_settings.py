import discord
from discord.ext import commands

from ...utils.utility import Color

class Config(commands.Cog):
    def __init__(self, bot, init) -> None:
        super().__init__()
        self.bot = bot
        self.init = init

        # We'll be having a config file for this for each lobby
    @commands.hybrid_command(name="settings", description="Shows and configure lobby settings")
    async def settings(self,ctx:commands.Context):
        """Base command for mygroup"""
        # Need validation if he's an owner and will pick a which lobby is this
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(color=Color.PRIMARY.to_discord_color(),description="Shows and configure lobby settings")
            embed.set_author(name="Ari connect - Settings", icon_url=self.bot.user.avatar.url)
            
            embed.add_field(name="Title",value="Set",inline=True)
            embed.add_field(name="Description",value="Set",inline=True)
            embed.add_field(name="Topics",value="Set",inline=True)

            embed.add_field(name="Chat Filter",value="0",inline=True)
            embed.add_field(name="Moderators",value="0",inline=True)
            embed.add_field(name="Ban List",value="0",inline=True)

            embed.add_field(name="Chat Logs",value="None",inline=True)
            embed.add_field(name="Action Logs",value="None",inline=True)
            embed.add_field(name="Player Report",value="None",inline=True)

            await ctx.send(embed=embed)

    
    