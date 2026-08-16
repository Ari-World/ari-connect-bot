import logging
import re
from typing import List, Optional, Tuple

from discord.ext import commands

from core.config import get_config
from ..domain.models import BannedContent, Connection, Lobby, LobbyConfig, ModeratorRole, MutedUser

log = logging.getLogger("globalchat.state")


class GlobalChatState:
    """In-memory cache of global_chat's data + pure query helpers.

    No Discord API calls, no database calls beyond the initial `load_data`.
    Discord-side logging/reporting lives in `services/audit_log_service.py`
    instead — this class only holds data and answers questions about it.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bypass_delete_listener = set()
        self.generalLobby = get_config().general_lobby_name
        # TODO: Move this somewhere maybe as a json file
        self.openworldThanksMessage = ("Thanks for connecting to the Open World Server! \n\n"+
        "**Remember to:** \n" +
        "> Be respectful and considerate. \n" +
        "> Protect your privacy. \n" +
        "> Follow our community guidelines.\n" +
        "> No NSFW or Lewd content\n"+
        "> Keep the chats Family Friendly and Clean\n\n"
        "If you see anyone breaking the rules, use ` /report ` and our global mods will take care of it!\n\n")

        self.prepareLogging()

    def prepareLogging(self):
        log.info("Preparing Logging IDs")
        config = get_config()
        self.guild_logging_id = config.log_guild_id
        self.chat_logging_id = config.log_chat_id
        self.system_logging_id = config.log_system_id
        self.mod_logging_id = config.log_mod_id
        self.player_report_logging_id = config.log_player_report_id

    async def load_data(
            self,
            lobby_repository,
            guild_repository,
            lobby_config_repository,
            muted_repository,
            malicious_urls_repository,
            malicious_words_repository,
            moderator_repository):

        self.lobby_data: List[Lobby] = await lobby_repository.findAll()
        self.connection: List[Connection] = await guild_repository.findAll()
        self.lobby_config: List[LobbyConfig] = await lobby_config_repository.findAll()
        self.muted_users: List[MutedUser] = await muted_repository.findAll()
        self.malicious_urls: List[BannedContent] = await malicious_urls_repository.findAll()
        self.malicious_words: List[BannedContent] = await malicious_words_repository.findAll()
        self.moderator: List[ModeratorRole] = await moderator_repository.findAll()

    def get_lobby_length(self, lobby_id: str) -> int:
        count = 0
        for connection in self.connection:
            if connection.lobby_id == lobby_id:
                count += 1
        return count

    def get_user_level(self, user_id) -> int:
        for role in self.moderator:
            for mod in role.mods:
                if mod.user_id == str(user_id):
                    return int(role.level)
        return 0

    def contains_malicious_url(self, content: str) -> Tuple[bool, Optional[str]]:
        if self.malicious_urls and self.malicious_words:
            for url in self.malicious_urls:
                if re.search(url.content, content, re.IGNORECASE):
                    return True, url.content

            for word in self.malicious_words:
                if word.content.lower() in content.lower():
                    return True, word.content

        return False, None

    def isUserBlackListed(self, id) -> Optional[MutedUser]:
        if self.muted_users:
            for user in self.muted_users:
                if user.id == id:
                    return user
        return None
