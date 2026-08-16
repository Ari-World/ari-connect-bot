from types import SimpleNamespace

from features.global_chat.services.relay_service import (
    build_relay_username,
    find_channel_in_document,
    prepare_reply_embed,
)


class TestFindChannelInDocument:
    def test_finds_the_matching_document(self):
        documents = [{"channel": 1, "message_id": 10}, {"channel": 2, "message_id": 20}]
        assert find_channel_in_document(documents, 2) == {"channel": 2, "message_id": 20}

    def test_returns_none_when_no_channel_matches(self):
        documents = [{"channel": 1, "message_id": 10}]
        assert find_channel_in_document(documents, 999) is None

    def test_returns_none_for_empty_documents(self):
        assert find_channel_in_document([], 1) is None


class TestBuildRelayUsername:
    def test_uses_global_name_when_present(self):
        author = SimpleNamespace(global_name="Global Name", name="username")
        assert build_relay_username(author, "My Server") == "Global Name || My Server"

    def test_falls_back_to_name_when_global_name_is_none(self):
        author = SimpleNamespace(global_name=None, name="username")
        assert build_relay_username(author, "My Server") == "username || My Server"

    def test_falls_back_to_name_when_global_name_is_missing_entirely(self):
        author = SimpleNamespace(name="username")
        assert build_relay_username(author, "My Server") == "username || My Server"


def make_message(content="hello", webhook_id=None, author_name="Someone", author_global_name="Global",
                  guild_name="Server", attachments=None):
    return SimpleNamespace(
        content=content,
        webhook_id=webhook_id,
        guild=SimpleNamespace(name=guild_name),
        author=SimpleNamespace(
            name=author_name,
            global_name=author_global_name,
            avatar=SimpleNamespace(url="http://avatar.png"),
        ),
        attachments=attachments or [],
    )


class TestPrepareReplyEmbed:
    def test_uses_webhook_author_name_when_relayed_message(self):
        message = make_message(webhook_id=123, author_name="RelayedName")
        embed = prepare_reply_embed(message)
        assert embed.author.name == "RelayedName"

    def test_uses_global_name_and_guild_when_not_a_webhook_message(self):
        message = make_message(webhook_id=None, author_global_name="Global", guild_name="My Server")
        embed = prepare_reply_embed(message)
        assert embed.author.name == "Global || My Server"

    def test_description_is_the_message_content(self):
        message = make_message(content="hi there")
        embed = prepare_reply_embed(message)
        assert embed.description == "hi there"

    def test_sets_image_from_a_supported_image_attachment(self):
        attachment = SimpleNamespace(filename="photo.png", url="http://img.png")
        message = make_message(attachments=[attachment])
        embed = prepare_reply_embed(message)
        assert embed.image.url == "http://img.png"

    def test_ignores_non_image_attachments(self):
        attachment = SimpleNamespace(filename="doc.pdf", url="http://doc.pdf")
        message = make_message(attachments=[attachment])
        embed = prepare_reply_embed(message)
        assert embed.image.url is None
