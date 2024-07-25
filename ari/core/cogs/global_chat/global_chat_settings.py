from discord.ext import commands

class Config(commands.Cog):
    def __init__(self, bot, init) -> None:
        super().__init__()
        self.bot = bot
        self.init = init
        
    @commands.hybrid_group(name="settings", description="Shows and configure lobby settings")
    async def settings(self,ctx:commands.Context):
        """Base command for mygroup"""
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid subcommand passed. Use `/settings` for more info.')

    @settings.command(name="testcommand", description="Test Command for settings")
    async def testcommand(self,ctx:commands.Context):
        await ctx.send("Setting command test")

    