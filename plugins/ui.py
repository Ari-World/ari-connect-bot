
import discord


class ConnectDropDown(discord.ui.View):
    lobby = None
    # ==============================================
    # Attemped to make it dynamic
    # Initial Idea

    # def __init__(self, options):
    #     super().__init__()
    #     self.options = options
        
    #     self.select = discord.ui.select(
    #         placeholder="Select a Lobby",
    #         options= self.generate_options(),
    #     )
    #     self.isRunning()

    # def isRunning(self):
    #     print(self.options)
    #     print("its running")

    # def generate_options(self):
    #     if self.options is None:
    #         return []
        
    #     return[discord.SelectOption(label=option, value=option) for option in self.options]

    @discord.ui.select(
        placeholder="Select a lobby",
        options = [
            discord.SelectOption(label="Toram Lobby 1", value="Toram Lobby 1"),
            discord.SelectOption(label="Toram Lobby 2", value="Toram Lobby 2"),
            discord.SelectOption(label="Cafe Lobby 1", value="Cafe Lobby 1"),
            discord.SelectOption(label="Cafe Lobby 2", value="Cafe Lobby 2"),
        ],
        min_values=1,
        max_values=1
    )
    async def getLobbies(self, interaction: discord.interactions ,select_item: discord.ui.select):
        self.lobby = select_item.values[0]
        await interaction.response.defer()
        self.stop()


class Choice(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="Yes" , style=discord.ButtonStyle.green)
    async def btn1(self, interaction: discord.interactions, btn:discord.ui.button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Back" , style=discord.ButtonStyle.red)
    async def btn2(self, interaction: discord.interactions, btn:discord.ui.button):
        self.value = False
        await interaction.response.defer()
        self.stop()
