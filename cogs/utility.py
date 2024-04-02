import discord, typing
from typing import Union, Optional
from discord.ext import commands
from discord import app_commands
import asyncio

class Utility(commands.Cog):
  def __init__(self, bot:commands.Bot):
    self.bot = bot


  @commands.hybrid_command(name='ping', description='Show the bot latency')
  async def ping(self, ctx):
    embed=discord.Embed(title="Bot Ping", description=f":magic_wand: My ping is {round(self.bot.latency*1000)}ms", color=0xff0000)
    await ctx.send(embed=embed)

  @commands.hybrid_command(name='avatar', description='Show the user avatar')
  async def avatar(self, ctx, user:Optional[Union[discord.Member, discord.User]]):
    if not user: user=ctx.author
    embed=discord.Embed(color=0x303236)
    embed.set_image(url=user.display_avatar.url)
    av_button=discord.ui.Button(label='Download', url=user.display_avatar.url, emoji='⬇️')
    view=discord.ui.View()
    view.add_item(av_button)
    await ctx.send(embed=embed, view=view)

  @commands.command(name="get_guild_name")
  async def get_guild_name(self, ctx, guild_id: int):
      try:
          guild = self.bot.get_guild(guild_id)
          guild_name = guild.name if guild else "Unknown Guild"
          await ctx.send(f"The name of the guild with ID {guild_id} is: {guild_name}.")
      except ValueError:
          await ctx.send("Invalid guild ID. Please enter a valid integer.")


  @commands.hybrid_command(name="server_list", description="Shows all server list")
  async def server_list(self, ctx):
      guilds = sorted(self.bot.guilds, key=lambda guild: len(guild.members), reverse=True)
      per_page = 10  # Number of guilds per page
      total_pages = (len(guilds) + per_page - 1) // per_page  # Calculate total pages
  
      page = 1  # Current page
  
      def get_embed(page_num):
          start_index = (page_num - 1) * per_page
          end_index = start_index + per_page
  
          embed = discord.Embed(
              title="Server List (Sorted by Member Count)",
              description=f"Page {page_num}/{total_pages}",
              color=discord.Color.green()
          )
  
          for guild in guilds[start_index:end_index]:
              member_count = len(guild.members)
              embed.add_field(
                  name=f"Server: {guild.name}",
                  value=f"Member Count: {member_count}",
                  inline=False
              )
  
          return embed
  
      message = await ctx.send(embed=get_embed(page))
      await message.add_reaction("⬅️")
      await message.add_reaction("➡️")
      await message.add_reaction("❌")
  
      def check(reaction, user):
          return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "❌"]
  
      while True:
          try:
              reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
  
              if str(reaction.emoji) == "➡️" and page != total_pages:
                  page += 1
                  await message.edit(embed=get_embed(page))
                  await message.remove_reaction(reaction, user)
  
              elif str(reaction.emoji) == "⬅️" and page > 1:
                  page -= 1
                  await message.edit(embed=get_embed(page))
                  await message.remove_reaction(reaction, user)
  
              elif str(reaction.emoji) == "❌":
                  await message.delete()
                  break
  
          except asyncio.TimeoutError:
              break
  
  
  



async def setup(bot:commands.Bot):
  await bot.add_cog(Utility(bot))