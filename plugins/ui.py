
import discord

# class ConnectLobbies(discord.ui.Select):
#     def __init__(self):
#         options = [
#             discord.SelectOption(label="Toram Lobby 1", value="Toram Lobby 1"),
#             discord.SelectOption(label="Toram Lobby 2", value="Toram Lobby 2"),
#             discord.SelectOption(label="Cafe Lobby 1", value="Cafe Lobby 1"),
#             discord.SelectOption(label="Cafe Lobby 2", value="Cafe Lobby 2"),
#         ]
        
#         super().__init__(
#             placeholder="Select a lobby",
#             options=options,
#             min_values=1,
#             max_values=1
#         )

#     async def callback(self, interaction: discord.Interaction, select_item : discord.ui.select):
#         selected_value = interaction.data["values"][0]
#         await interaction.response.send_message(f"You chose `{self.values[0]}`")

class ConnectDropDown(discord.ui.View):
    lobby = None

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
