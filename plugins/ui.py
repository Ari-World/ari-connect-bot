
import discord


class ConnectDropDown(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.lobby = None

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
        if interaction.user == self.author:
            self.lobby = select_item.values[0]
            await interaction.response.defer()
            self.stop()


class Choice(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.value = None

    @discord.ui.button(label="Yes" , style=discord.ButtonStyle.green)
    async def btn1(self, interaction: discord.interactions, btn:discord.ui.button):
        if interaction.user == self.author:
            self.value = True
            await interaction.response.defer()
            self.stop()

    @discord.ui.button(label="Back" , style=discord.ButtonStyle.red)
    async def btn2(self, interaction: discord.interactions, btn:discord.ui.button):
        if interaction.user == self.author:
            self.value = False
            await interaction.response.defer()
            self.stop()
