"""Unit tests for GuildConnectionService using hand-written fakes instead of
a mocking framework, per the PRD's testing decisions. No real Discord
connection or database involved — just plain objects shaped like the ones
discord.py/the repository layer would hand us.
"""
import asyncio

from features.global_chat.domain.models import Connection
from features.global_chat.services.guild_connection_service import GuildConnectionService
from features.global_chat.persistence.state import GlobalChatState


class FakeWebhook:
    def __init__(self, url):
        self.url = url
        self.deleted = False

    async def delete(self):
        self.deleted = True


class FakeChannel:
    def __init__(self, channel_id, webhook_url="https://discord.com/api/webhooks/1/token", existing_webhooks=None):
        self.id = channel_id
        self._webhook_url = webhook_url
        self._existing_webhooks = existing_webhooks or []
        self.created_webhook_name = None

    async def create_webhook(self, name):
        self.created_webhook_name = name
        return FakeWebhook(self._webhook_url)

    async def webhooks(self):
        return self._existing_webhooks


class FakeGuild:
    def __init__(self, guild_id, name):
        self.id = guild_id
        self.name = name


class FakeGuildRepository:
    """Mirrors the real repository's create() contract: takes a Connection,
    sets its _id, returns the same entity."""
    def __init__(self):
        self.created = []
        self.deleted = []

    async def create(self, connection):
        connection._id = "fake-id"
        self.created.append(connection)
        return connection

    async def delete(self, connection):
        self.deleted.append(connection)


class FakeRepository:
    def __init__(self):
        self.guild_repository = FakeGuildRepository()


class FakeBot:
    def __init__(self, channel=None):
        self._channel = channel

    def get_channel(self, channel_id):
        return self._channel


def make_state():
    state = GlobalChatState.__new__(GlobalChatState)
    state.connection = []
    return state


class TestConnect:
    def test_creates_a_webhook_persists_and_caches_the_connection(self):
        state = make_state()
        repo = FakeRepository()
        channel = FakeChannel(channel_id=10)
        guild = FakeGuild(guild_id=1, name="Server A")
        service = GuildConnectionService(FakeBot(), state, repo)

        result = asyncio.run(service.connect(channel, guild, "abc", "My Lobby"))

        assert channel.created_webhook_name == "My Lobby"
        assert result.lobby_id == "abc"
        assert result.channel_id == 10
        assert result.guild_id == 1
        assert result.guild_name == "Server A"
        assert result in state.connection
        assert repo.guild_repository.created == [result]


class TestDisconnect:
    def test_deletes_the_matching_webhook_and_removes_the_connection(self):
        state = make_state()
        repo = FakeRepository()
        connection = Connection(channel_id=10, webhook="https://discord.com/api/webhooks/1/token", lobby_id="abc", guild_id=1, guild_name="Server A")
        state.connection = [connection]
        existing_webhook = FakeWebhook("https://discord.com/api/webhooks/1/token")
        channel = FakeChannel(channel_id=10, existing_webhooks=[existing_webhook])
        service = GuildConnectionService(FakeBot(channel), state, repo)

        asyncio.run(service.disconnect(connection))

        assert existing_webhook.deleted is True
        assert connection not in state.connection
        assert repo.guild_repository.deleted == [connection]

    def test_handles_a_missing_channel_gracefully(self):
        state = make_state()
        repo = FakeRepository()
        connection = Connection(channel_id=10, webhook="url", lobby_id="abc", guild_id=1, guild_name="A")
        state.connection = [connection]
        service = GuildConnectionService(FakeBot(channel=None), state, repo)

        asyncio.run(service.disconnect(connection))

        assert connection not in state.connection
        assert repo.guild_repository.deleted == [connection]


class TestSwitch:
    def test_disconnects_old_and_connects_new(self):
        state = make_state()
        repo = FakeRepository()
        old_connection = Connection(channel_id=10, webhook="https://discord.com/api/webhooks/1/token", lobby_id="old", guild_id=1, guild_name="Server A")
        state.connection = [old_connection]
        channel = FakeChannel(channel_id=10)
        guild = FakeGuild(guild_id=1, name="Server A")
        service = GuildConnectionService(FakeBot(channel), state, repo)

        result = asyncio.run(service.switch(channel, guild, old_connection, "new", "New Lobby"))

        assert old_connection not in state.connection
        assert result in state.connection
        assert result.lobby_id == "new"
        assert channel.created_webhook_name == "New Lobby"
