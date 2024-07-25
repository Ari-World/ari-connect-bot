import datetime
import discord
from discord.ext import commands
from ...utils.utility import Color

class Info(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="support",with_app_command=True,description="Join our support server")
    async def support(self,ctx:commands.Context):
        embed = discord.Embed(color=Color.PRIMARY.to_discord_color())
        embed.set_author(name="Ari connect support server", icon_url=self.bot.user.avatar.url)
        embed.add_field(name="",value="[Click here](https://discord.gg/w8XKwkZQza) to join our support server")

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Support Server", style=discord.ButtonStyle.link, url= "https://discord.gg/w8XKwkZQza"))
        
        await ctx.interaction.response.send_message(embed=embed,view=view)

    @commands.hybrid_command(name="invite", with_app_command=True, description="Invite Ari to your server")
    async def invite(self,ctx:commands.Context):
        embed = discord.Embed(color=Color.PRIMARY.to_discord_color())
        embed.add_field(name="",value=f"[Invite Link]({self.bot.inv_url})")
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite", style=discord.ButtonStyle.link, url=self.bot.inv_url))
        
        await ctx.interaction.response.send_message(embed=embed,view=view)