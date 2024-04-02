import pymongo
import random
import json
import discord, typing, os
from typing import *
from utility.db import db
from discord.ext import commands, tasks
from keep_alive import keep_alive
from discord import Intents
from discord import app_commands
import secrets


class MyBot(commands.Bot):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.db=db
    
  async def on_ready(self):
    guild_count = len(bot.guilds)
    member_count = sum(len(guild.members) for guild in bot.guilds)

    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"over {guild_count} Guilds with {member_count} Members!"
    )
    await bot.change_presence(
        status=discord.Status.online,
        activity=activity
    )
    print("Ari Toram is Online")
  
  async def setup_hook(self):
      await self.load_extension("cogs.open_world_server")
  
      cog_files = [fn for fn in os.listdir('./cogs') if fn.endswith('.py') and not fn.startswith('open_world_server')]
      for fn in cog_files:
          await self.load_extension(f"cogs.{fn[:-3]}")

intents = Intents.all()
bot = MyBot(command_prefix=commands.when_mentioned_or("a!","A!"), intents=intents, help_command=None)

@bot.event
async def on_guild_join(guild):
  print(f'Bot has been added to a new server {guild.name}')
  user = await bot.fetch_user(886682391308026006)
  await user.send(f'**Bot has been added to a new server:**\n{guild.name}')
  text_channel = random.choice(guild.text_channels)
  await text_channel.send(f"💖 **Thank you for inviting {bot.user.name}!!**\n\n__**A brief intro**__\nHey Everyone! My main purpose is creating an Inter Guild / Server Connectivity to bring the world closer together!\nHope you'll find my application useful! Thankyouuu~\n\nType `a!about` to know more about me and my usage!\n\n**__Servers Connected__**\n{len(bot.guilds)}\n\n*Kindly contact the bot's developer in case of any help : _flamesz*")

@bot.tree.context_menu(name='Report Message')
async def reportmessage(interaction: discord.Interaction, message: discord.Message):
  report_channel = bot.get_channel(975254983559766086)
  user = interaction.user
  if message.attachments:
    for attachment in message.attachments:
      content = f'🚩 ***Report by : {user}***\n{message.content}\n{attachment.url}'
  else:
    content = f"🚩 ***Report by : {user}***\n{message.content}"
  await report_channel.send(content)
  await interaction.response.send_message(f'*Report sent to mods. Please maintain friendly environment*', ephemeral=True)
  
#COOLDOWN ERROR!
@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandOnCooldown):
		msg = '**Command on cooldown** Retry after **{:.2f}s**'.format(
		    error.retry_after)
		await ctx.send(msg)

@bot.command(aliases=["dev"])
async def developer(ctx):
	await ctx.send("developer of this bot is _flamesz")

@bot.hybrid_command(name="about",description="About Ari Toram")
async def about_us(ctx):
    server_count = len(bot.guilds)
    member_count = sum(guild.member_count for guild in bot.guilds)

    message = (
        "🌍 **Introducing the Ari Connect: Your Gateway to a Global Chat Experience!** 🤖🌐\n\n"
        "✨ Connect and Unite: Experience the thrill of a unified Global Chat by connecting various servers into one channel with Ari Connect. 🚀\n\n"
        "🔥 Public Lobbies: Engage in lively conversations, seek assistance, and make new friends across the servers in the vibrant public lobbies. 🌟\n\n"
        "🔒 Private Spaces: Create secure and exclusive private lobbies for your alliance/partner servers. Simply provide a lobby name and password to the developer for a private connection. *Conditions applied 🗝️\n\n"
        "💫 Effortless Switching: Seamlessly transition to private lobbies by connecting to a public lobby first, then switch using the exact name and password. ⚡️\n\n"
        "Integrate the Ari Connect into your server today and unlock a whole new level of communication. 🌐🔥 "
        "Connect, collaborate, and conquer the global world with members from all corners of the globe. Let the adventure begin!\n\n"
        "**Steps (Slash Commands):**\n"
        "> 1. Create a channel for Toram Global Chat.\n"
        "> 2. Connect to the channel using the command: `/connect #channel`.\n"
        "> 3. Check available lobbies with the command: `/lobbies`.\n"
        "> 4. Switch to a lobby using the command: `/switch \"Lobby Name\"` or start chatting in the current lobby.\n\n"
        f"**Server Count: {server_count}**\n"
        f"**Member Count: {member_count}**\n\n"
        "*Kindly contact the bot's developer in case of any help : _flamesz*\n"
        "*Please watch the tutorial video below with sound! 👇*"
    )
    file_path = "./utility/Video_Guide.mp4"

    await ctx.send(message,file=discord.File(file_path))


# @bot.command(aliases=['invitation'], brief="Creates an invite link to the channel (Admins Only)")
# @commands.has_permissions(administrator = True)
# async def devinv(ctx):
#     embed = discord.Embed(
#     description = "[Click me to invite me to your server!](https://discord.com/api/oauth2/authorize?client_id=895242125208342548&permissions=8&scope=applications.commands%20bot)",
#     colour=000)
  
#     await ctx.send(embed=embed, delete_after=15)


#---------------------------------------------------------------------------------------------------#

    
@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
  ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":

            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)

        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

# Works like:
# !sync -> global sync
# !sync ~ -> sync current guild
# !sync * -> copies all global app commands to current guild and syncs
# !sync ^ -> clears all commands from the current guild target and syncs (removes guild commands)
# !sync id_1 id_2 -> syncs guilds with id 1 and 2

#---------------------------------------------------------------------------------------------------#    


while __name__=='__main__': 
  try:
    keep_alive()
    bot.run(os.environ['TOKEN'])
  except discord.errors.HTTPException as e:
    print(e)
    print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
    os.system('kill 1')