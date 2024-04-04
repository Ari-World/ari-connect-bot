import os
import discord
from discord import Intents
from discord.ext import commands

class AriBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.intents = Intents.all()

        # Cogs Informations
        self._extensions = [x.replace('.py', '') for x in os.listdir('cogs') if x.endswith('.py')]
        
        # Load the cogs
        self.load_extension()
    
    # ------------------------------- Methods -------------------------------------------------
    def load_extension():
        print("Something")


    # ------------------------------- Events -------------------------------------------------
    async def on_ready(self):
        # Some Logics here
        print("Ari Toram is Online")

    
    async def on_guild_join(guild):
        print(f'Bot has been added to a new server {guild.name}')
        user = await bot.fetch_user(886682391308026006)
        await user.send(f'**Bot has been added to a new server:**\n{guild.name}')
        text_channel = random.choice(guild.text_channels)
        await text_channel.send(f"💖 **Thank you for inviting {bot.user.name}!!**\n\n__**A brief intro**__\nHey Everyone! My main purpose is creating an Inter Guild / Server Connectivity to bring the world closer together!\nHope you'll find my application useful! Thankyouuu~\n\nType `a!about` to know more about me and my usage!\n\n**__Servers Connected__**\n{len(bot.guilds)}\n\n*Kindly contact the bot's developer in case of any help : _flamesz*")

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
    
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            msg = '**Command on cooldown** Retry after **{:.2f}s**'.format(
                error.retry_after)
            await ctx.send(msg)
    # ------------------------------- Commands -------------------------------------------------

    @commands.command(aliases=["dev"])
    async def developer(ctx):
        await ctx.send("developer of this bot is _flamesz")
        print("test")

    @commands.hybrid_command(name="about", description="About Ari Toram")
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

        
if __name__ == '__main__':
    AriBot.init()