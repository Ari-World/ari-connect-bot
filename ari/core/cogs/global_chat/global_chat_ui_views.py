
## View
import asyncio
import logging
import discord
from discord import ui
from .global_chat_repository import Repository 
from ...utils.utility import generate_uuid
log = logging.getLogger("globalchat.view")



class CreateLobbyModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title='Create Lobby')  # Properly initialize the base class with the title

        self.data = {
            "title": "",
            "description": "",
        }
        
        self.name = discord.ui.TextInput(
            label='Lobby name',
            placeholder='Enter lobby name',
            max_length=100
        )
        self.topics = discord.ui.TextInput(
            label='Topics',
            placeholder='Separate your topics with spaces (write all you can think)',
            max_length=100
        )
        self.description = discord.ui.TextInput(
            label='Description',
            style=discord.TextStyle.paragraph,
            placeholder='Describe your lobby',
        )
        
        
        # Add items to the modal
        self.add_item(self.name)
        self.add_item(self.topics)
        self.add_item(self.description)

 
    async def on_submit(self, interaction: discord.Interaction):
        lobby_code = generate_uuid()
        channel = interaction.channel

        # Generate lobby data
        self.data["title"] = self.name.value
        self.data["description"] = self.description.value
        self.data["topics"] = self.topics.value.split(" ")
        self.data["limit"] = 20
        self.data["guild_id"] = interaction.guild.id
        self.data["guild_name"] = interaction.guild.name
        self.data['lobby_id'] = lobby_code
        self.data["owner_id"] = interaction.user.id
        
        db = Repository()
        await db.lobby_repository.create(self.data)

        # Creating connection data
        webhook = await channel.create_webhook(name=self.name.value)
        self.connection = {
            "lobby_id": lobby_code,
            "channel_id": channel.id,
            "webhook": webhook.url,
            "guild_name": interaction.guild.name
        }

        await db.guild_repository.create(self.connection)
        # Sending a information for created lobby
        topics = ""
        for data in  self.data["topics"]:
            topics += f"`{data}` "

        embed = discord.Embed(
            title= self.name.value, 
            description="> **Connections:** `1/20` \n"
                        f"> **Lobby code:** {lobby_code}",
            color=0xFFC0CB
        )

        embed.add_field(name="Topics", value=topics, inline=False)
        embed.add_field(name="Description", value=self.description.value, inline=False)
        embed.set_footer(text=f"For futher configuration do /config <lobbycode>",icon_url=interaction.user.avatar.url)
        
        await interaction.response.send_message(embed=embed)
        
        
class LobbyDropDown(discord.ui.Select):
    def __init__(self,server_lobbies,author, on_item_added):
        self.server_lobbies = server_lobbies
        self.author = author
        self.on_item_added = on_item_added
        
        options = [discord.SelectOption(label=lobby["lobbyname"], value=lobby["lobbyname"]) for lobby in self.server_lobbies]
        super().__init__(
            placeholder="Select a lobby",
            options=options,
            min_values=1,
            max_values=1
        )
    async def callback(self, interaction):
        if interaction.user == self.author:
            await interaction.response.defer()
            await self.on_item_added(interaction.data['values'][0])
                 
class ConnectDropDown(discord.ui.View):
    def __init__(self, author, server_lobbies):
        super().__init__()
        self.lobby = None
        self.add_item(LobbyDropDown(server_lobbies,author, self.on_item_added))

    async def on_item_added(self,value):
        self.lobby = value
        self.stop()

class DynamicChoice(discord.ui.View):
    def __init__(self, author, choices):
        super().__init__()
        self.author = author
        self.value = None
        
        # Dynamically create buttons based on the provided choices
        for choice in choices:
            self.add_item(self.create_button(choice))
    
    def create_button(self, label):
        # Create a button with the given label
        button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
        button.callback = self.button_callback
        return button

    async def button_callback(self, interaction: discord.Interaction):
        if interaction.user == self.author:
            # Find the button that was clicked by matching custom_id
            for x in interaction.message.components:
                for button in x.children:
                    if button.custom_id == interaction.data['custom_id']:
                        self.value = button.label
            await interaction.response.defer()
            self.stop()
