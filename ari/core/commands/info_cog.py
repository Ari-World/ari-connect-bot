import datetime
import discord
from discord.ext import commands
from ..utils.chat_formatting import humanize_timedelta
from ..utils.utility import Color

class Info(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="stats", with_app_command=True, description="Shows bot statistics")
    async def stats(self, ctx: commands.Context):
        guild_count = len(self.bot.guilds)
        user_count = len(set(self.bot.get_all_members())) if self.bot.intents.members else None

        now = datetime.datetime.now(datetime.timezone.utc)
        delta = now - self.bot.uptime
        uptime_str = humanize_timedelta(timedelta=delta)

        embed = discord.Embed(color=Color.PRIMARY.to_discord_color())
        embed.set_author(name="Ari Connect", icon_url=self.bot.user.avatar.url)
        embed.add_field(name="Servers", value=str(guild_count))
        if user_count is not None:
            embed.add_field(name="Users", value=str(user_count))
        embed.add_field(name="Uptime", value=uptime_str)
        embed.add_field(name="discord.py", value=discord.__version__)
        await ctx.send(embed=embed)

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