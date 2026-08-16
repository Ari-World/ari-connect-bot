from features.global_chat.ui import presenters
from features.global_chat.domain.models import LobbyDetails, LogChannel, LogConfig, ModerationConfig


class TestBuildMenuEmbed:
    def test_title_and_description(self):
        embed = presenters.build_menu_embed("Settings", "http://icon.png", "A description")
        assert embed.author.name == "Ari connect - Settings"
        assert embed.description == "A description"

    def test_fields_are_rendered(self):
        fields = [{"emoji": "🔎", "title": "Lobby Details", "description": "Edit", "inline": True}]
        embed = presenters.build_menu_embed("Settings", "http://icon.png", fields=fields)
        assert len(embed.fields) == 1
        assert embed.fields[0].name == "🔎 Lobby Details"
        assert embed.fields[0].value == "Edit"

    def test_no_fields_means_no_fields(self):
        embed = presenters.build_menu_embed("Settings", "http://icon.png")
        assert len(embed.fields) == 0


class TestLobbyDetailsFields:
    def test_reads_title_description_topics(self):
        fields = presenters.lobby_details_fields(
            LobbyDetails(title="My Lobby", description="A place to chat", topics=["gaming", "chill"])
        )
        values = {f["value"]: f["description"] for f in fields}
        assert "My Lobby" in values["title"]
        assert "A place to chat" in values["description"]
        assert "gaming" in values["topics"]


class TestModerationFields:
    def test_reads_the_actual_schema_key_banned_server_not_banned_servers(self):
        # CreateLobbyModal creates "banned_server" (singular) in moderation_config —
        # the original cog code referenced "banned_servers" (plural), which would
        # KeyError. This locks in the corrected key.
        fields = presenters.moderation_fields(
            ModerationConfig(moderators=[1], banned_words=[], banned_links=[], banned_users=[], banned_server=[1, 2])
        )
        counts = {f["value"]: f["description"] for f in fields}
        assert "1" in counts["moderators"]
        assert "2" in counts["bannedservers"]


class TestLoggingFields:
    def test_reads_the_actual_schema_key_moderation_log_not_moderation_logs(self):
        # CreateLobbyModal creates "moderation_log" (singular) — the original cog
        # code referenced "moderation_logs" (plural), which would KeyError.
        fields = presenters.logging_fields(LogConfig(
            chat_log=LogChannel(channel_id=111),
            moderation_log=LogChannel(channel_id=222),
            report_logs=LogChannel(channel_id=333),
        ))
        channel_ids = {f["value"]: f["description"] for f in fields}
        assert "111" in channel_ids["chatlogs"]
        assert "222" in channel_ids["moderationlogs"]
        assert "333" in channel_ids["reportlogs"]
