
import discord

class ConnectLobbies(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Toram Lobby 1", value="Toram Lobby 1"),
            discord.SelectOption(label="Toram Lobby 2", value="Toram Lobby 2"),
            discord.SelectOption(label="Cafe Lobby 1", value="Cafe Lobby 1"),
            discord.SelectOption(label="Cafe Lobby 2", value="Cafe Lobby 2"),
        ]
        
        super().__init__(
            placeholder="Select a lobby",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        selected_value = interaction.data["values"][0]
        

class ConnectDropDown(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ConnectLobbies())
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
