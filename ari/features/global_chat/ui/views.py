
## View
import asyncio
import logging
from typing import List
import discord
from discord import ui
from discord.ext import commands
from core.utils.utility import generate_uuid
from . import presenters
log = logging.getLogger("globalchat.view")
# This is currently worked only only for creating lobby
class CreateLobbyModal(discord.ui.Modal):
    def __init__(self, lobby_service, guild_connection_service):
        super().__init__(title='Create Lobby')  # Properly initialize the base class with the title
        self.lobby_service = lobby_service
        self.guild_connection_service = guild_connection_service

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
        topics = self.topics.value.split(" ")

        await self.lobby_service.create_lobby(
            lobby_id=lobby_code,
            guild_id=interaction.guild.id,
            guild_name=interaction.guild.name,
            owner_id=interaction.user.id,
            title=self.name.value,
            description=self.description.value,
            topics=topics,
        )

        await self.guild_connection_service.connect(channel, interaction.guild, lobby_code, self.name.value)

        embed = presenters.build_lobby_created_embed(self.name.value, lobby_code, self.description.value, topics)
        embed.set_footer(text="For futher configuration do /config <lobbycode>", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed)

class LobbyPagination(discord.ui.View):
    def __init__(self,  lobby_service, current_page: int = 1, sep: int = 5, timeout=None):
        super().__init__()
        self.lobby_service = lobby_service

        self.data : List = []

        self.current_page = current_page
        self.sep = sep
        self.timeout = timeout
        # Create the data

    def load_data(self):
        self.data = self.lobby_service.list_lobby_summaries()

    async def send(self, ctx: commands.Context):
        self.message = await ctx.send(view=self)
        log.info(self.data)
        await self.update_message(self.data[:self.sep])

    def create_embed(self, data):
        total_pages = int(len(data) / self.sep) + 1
        icon_url = self.message.author.avatar.url if self.message.author.avatar else None
        return presenters.build_lobby_pagination_embed(data, self.current_page, total_pages, icon_url)

    async def update_message(self, data):
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(data),view=self)

    def update_buttons(self):
        if self.current_page == 1:
            self.first_page_button.disabled = True
            self.prev_button.disabled = True
            self.first_page_button.style = discord.ButtonStyle.gray
            self.prev_button.style = discord.ButtonStyle.gray
        else:
            self.first_page_button.disabled = False
            self.prev_button.disabled = False
            self.first_page_button.style = discord.ButtonStyle.green
            self.prev_button.style = discord.ButtonStyle.primary

        if self.current_page == int(len(self.data) / self.sep) + 1:
            self.next_button.disabled = True
            self.last_page_button.disabled = True
            self.last_page_button.style = discord.ButtonStyle.gray
            self.next_button.style = discord.ButtonStyle.gray
        else:
            self.next_button.disabled = False
            self.last_page_button.disabled = False
            self.last_page_button.style = discord.ButtonStyle.green
            self.next_button.style = discord.ButtonStyle.primary
    
    def get_current_page_data(self):
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        if not self.current_page == 1:
            from_item = 0
            until_item = self.sep
        if self.current_page == int(len(self.data) / self.sep) + 1:
            from_item = self.current_page * self.sep - self.sep
            until_item = len(self.data)
        return self.data[from_item:until_item]
    
    # TODO : Add input to put the lobby code

    @discord.ui.button(label="|<",
                       style=discord.ButtonStyle.green)
    async def first_page_button(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = 1

        await self.update_message(self.get_current_page_data())

    @discord.ui.button(label="<",
                       style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page -= 1
        await self.update_message(self.get_current_page_data())

    @discord.ui.button(label=">",
                       style=discord.ButtonStyle.primary)
    async def next_button(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page += 1
        await self.update_message(self.get_current_page_data())

    @discord.ui.button(label=">|",
                       style=discord.ButtonStyle.green)
    async def last_page_button(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = int(len(self.data) / self.sep) + 1
        await self.update_message(self.get_current_page_data())
        
class DropDown(discord.ui.Select):
    def __init__(
            self, 
            items: List, 
            author, 
            placeholder: str, 
            on_item_added
    )-> None:
        self.items = items
        self.author = author
        self.on_item_added = on_item_added
        
        options = [discord.SelectOption(label=item["title"], value=item["value"], emoji=item['emoji']) for item in self.items]
        
        super().__init__(
            placeholder=placeholder,
            options=options,
            min_values=1,
            max_values=1
        )
    async def callback(self, interaction):
        if interaction.user == self.author:
            # This stops the interaction failed error
            await interaction.response.defer()
            
            await self.on_item_added(interaction.data['values'][0])
                 
class DynamicDropDown(discord.ui.View):
    def __init__(
            self, 
            author, 
            items:List, 
            placeholder: str
    ) -> None:
        super().__init__()
        self.value = None
        self.add_item(DropDown(items, author, placeholder, self.on_item_added))

    async def on_item_added(self,value):
        self.value = value
        self.stop()

class DynamicChoice(discord.ui.View):
    def __init__(self, author, choices,timeout=60):
        super().__init__()        
        self.timeout = timeout
        self.author = author
        self.value = None
        
        # Dynamically create buttons based on the provided choices
        for choice in choices:
            self.add_item(self.create_button(choice))
    
    def create_button(self, choice):
        # Create a button with the given label
        button = discord.ui.Button(label=choice['title'], style=choice['color'])
        button.callback = self.button_callback
        return button

    async def button_callback(self, interaction: discord.Interaction):
        if interaction.user == self.author:
            # Find the button that was clicked by matching custom_id
            for button in self.children:
                if button.custom_id == interaction.data['custom_id']:
                    self.value = button.label
                    button.style = discord.ButtonStyle.primary
                    break
            await interaction.response.defer()
            self.stop()