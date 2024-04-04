import os
import random
import discord
from discord import Intents

from discord.ext import commands

class Ari(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="a!",intents=self._create_intents())
        
    def _create_intents(self):
        intents = Intents.all()
        intents.message_content = True
        return intents

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

        print(f'We have logged in as {self.user}')
        
    async def on_guild_join(self,guild):
        print(f'Bot has been added to a new server {guild.name}')
        # user = await bot.fetch_user(886682391308026006)
        # await user.send(f'**Bot has been added to a new server:**\n{guild.name}')
        text_channel = 1225530837131329536
        await text_channel.send(f"💖 **Thank you for inviting {bot.user.name}!!**\n\n__**A brief intro**__\nHey Everyone! My main purpose is creating an Inter Guild / Server Connectivity to bring the world closer together!\nHope you'll find my application useful! Thankyouuu~\n\nType `a!about` to know more about me and my usage!\n\n**__Servers Connected__**\n{len(bot.guilds)}\n\n*Kindly contact the bot's developer in case of any help : _flamesz*")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')


    # @commands.command(name="about",description="About Ari Toram")
    # async def about_us(self,ctx):
    #     print("test")
    #     server_count = len(bot.guilds)
    #     member_count = sum(guild.member_count for guild in bot.guilds)

    #     message = (
    #         "🌍 **Introducing the Ari Connect: Your Gateway to a Global Chat Experience!** 🤖🌐\n\n"
    #         "✨ Connect and Unite: Experience the thrill of a unified Global Chat by connecting various servers into one channel with Ari Connect. 🚀\n\n"
    #         "🔥 Public Lobbies: Engage in lively conversations, seek assistance, and make new friends across the servers in the vibrant public lobbies. 🌟\n\n"
    #         "🔒 Private Spaces: Create secure and exclusive private lobbies for your alliance/partner servers. Simply provide a lobby name and password to the developer for a private connection. *Conditions applied 🗝️\n\n"
    #         "💫 Effortless Switching: Seamlessly transition to private lobbies by connecting to a public lobby first, then switch using the exact name and password. ⚡️\n\n"
    #         "Integrate the Ari Connect into your server today and unlock a whole new level of communication. 🌐🔥 "
    #         "Connect, collaborate, and conquer the global world with members from all corners of the globe. Let the adventure begin!\n\n"
    #         "**Steps (Slash Commands):**\n"
    #         "> 1. Create a channel for Toram Global Chat.\n"
    #         "> 2. Connect to the channel using the command: `/connect #channel`.\n"
    #         "> 3. Check available lobbies with the command: `/lobbies`.\n"
    #         "> 4. Switch to a lobby using the command: `/switch \"Lobby Name\"` or start chatting in the current lobby.\n\n"
    #         f"**Server Count: {server_count}**\n"
    #         f"**Member Count: {member_count}**\n\n"
    #         "*Kindly contact the bot's developer in case of any help : _flamesz*\n"
    #         "*Please watch the tutorial video below with sound! 👇*"
    #     )
    #     file_path = "./utility/Video_Guide.mp4"

    #     await ctx.send(message,file=discord.File(file_path))

    # @commands.command(aliases=["dev"])
    # async def developer(self,ctx):
    #     print("test")
    #     await ctx.send("developer of this bot is _flamesz")
    # @commands.command()
    # async def ping(self, ctx):
    #     await ctx.send('pong')
        

    # Gonna Disassemble
    # async def setup_hook(self):
    #   await self.load_extension("cogs.open_world_server")

    #   cog_files = [fn for fn in os.listdir('./cogs') if fn.endswith('.py') and not fn.startswith('open_world_server')]
    #   for fn in cog_files:
    #       await  self.load_extension(f"cogs.{fn[:-3]}")


if __name__ == "__main__":
    bot = Ari()
    bot.run('')


