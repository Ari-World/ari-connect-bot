import discord, typing
from typing import Union, Optional
from discord.ext import commands
from discord import app_commands
import asyncio

class GlobalUtility(commands.Cog):
  def __init__(self, bot:commands.Bot):
    self.bot = bot
    self.openworld_cog = bot.get_cog("OpenWorldServer")
    self.private_lobbies = self.openworld_cog.private_lobbies
    self.server_lobbies = self.openworld_cog.server_lobbies
    self.lobby_limits = self.openworld_cog.lobby_limits
    self.get_lobby_limit = self.openworld_cog.get_lobby_limit
    self.find_guild = self.openworld_cog.find_guild
    self.per_page = 5
  
  @commands.hybrid_command(name='guilds', description="Learn more about connected guilds!")
  async def guilds_command(self, ctx, selected_lobby=None):
    guilds_data = await self.bot.db.guilds_collection.find().to_list(length=None)
    guild_info = []

    for guild_data in guilds_data:
        server_name = guild_data["server_name"]
        channels = guild_data["channels"]
        lobby_names = []

        for channel in channels:
            lobby_name = channel["lobby_name"]

            if lobby_name in self.private_lobbies:
                lobby_name = ":lock: Private Lobby"  # Display as locked private lobby

            lobby_names.append(lobby_name)

        guild_info.append((server_name, lobby_names))

    if selected_lobby:
        filtered_guilds = [(server_name, lobby_names) for server_name, lobby_names in guild_info if selected_lobby in lobby_names]
    else:
        filtered_guilds = guild_info

    total_pages = (len(filtered_guilds) + self.per_page - 1) // self.per_page  # Calculate total pages
    page = 0  # Current page

    embed = discord.Embed(title=f"🌏 Information of {len(filtered_guilds)} Guilds Found", color=discord.Color.blue())
    message = None

    while True:
        embed.clear_fields()

        start_index = page * self.per_page
        end_index = min(start_index + self.per_page, len(filtered_guilds))

        for i, (server_name, lobby_names) in enumerate(filtered_guilds[start_index:end_index], start=start_index):
            value = "\n".join(lobby_names)
            embed.add_field(name=f"#{i+1} {server_name}", value=value, inline=False)

        embed.set_footer(text=f"Page {page + 1}/{total_pages}")

        if message:
            await message.edit(embed=embed)
        else:
            message = await ctx.send(embed=embed)

        previous_emoji = "⬅️"
        next_emoji = "➡️"
        close_emoji = "❌"

        await message.add_reaction(previous_emoji)
        await message.add_reaction(next_emoji)
        await message.add_reaction(close_emoji)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in [previous_emoji, next_emoji, close_emoji]

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            await message.clear_reactions()

            if str(reaction.emoji) == previous_emoji and page > 0:
                page -= 1
            elif str(reaction.emoji) == next_emoji and page < total_pages - 1:
                page += 1
            elif str(reaction.emoji) == close_emoji:
                await message.delete()
                break
        except asyncio.TimeoutError:
            break

  @guilds_command.error
  async def guilds_command_error(self, ctx, error):
      if isinstance(error, commands.MissingRequiredArgument):
          await self.guilds_command(ctx)


  @commands.hybrid_command(name='lobbies', description='Show all lobby strength')
  async def lobby_strength(self, ctx):
      guild_id = ctx.guild.id
      channel_id = ctx.channel.id

      existing_guild = await self.find_guild(guild_id, channel_id)
      current_lobby = ""
      if existing_guild:
          channels = existing_guild.get("channels", [])
          for channel in channels:
              if channel["channel_id"] == channel_id:
                  current_lobby = channel["lobby_name"]
                  break

      lobby_strengths = {lobby: {"count": 0, "limit": self.get_lobby_limit(lobby)} for lobby in self.server_lobbies}
      private_lobby_count = len(self.private_lobbies)
      private_lobby_members = 0  # Initialize the count of private lobby members

      async for document in self.bot.db.guilds_collection.find():
          channels = document.get("channels", [])
          for channel in channels:
              lobby_name = channel.get("lobby_name")
              if lobby_name in lobby_strengths:
                  lobby_strengths[lobby_name]["count"] += 1
              elif lobby_name in self.private_lobbies:  # Check if lobby is a private lobby
                  private_lobby_members += 1

      embed = discord.Embed(title="Lobby Strengths", color=discord.Color.green())

      for lobby in self.server_lobbies:
          count = lobby_strengths[lobby]["count"]
          limit = lobby_strengths[lobby]["limit"]
          emoji = ":red_circle:" if count >= limit else ":orange_circle:" if count >= limit/2 else ":green_circle:"
          lobby_display_name = lobby
          if lobby == current_lobby:
              lobby_display_name += " (Your Guild Lobby)"
          embed.add_field(name=f"{emoji} {lobby_display_name}", value=f"{count}/{limit} Guilds Connected", inline=False)

      private_lobby_display = f":lock: Private Lobbies: {private_lobby_count}\nMembers: {private_lobby_members}"
      embed.add_field(name="\u200b", value=private_lobby_display, inline=False)

      await ctx.send(embed=embed)



async def setup(bot:commands.Bot):
    await bot.add_cog(GlobalUtility(bot))