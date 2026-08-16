from types import SimpleNamespace

from core import presenters


def make_guild(name="Test Guild", owner_name="OwnerName", owner_id=999):
    return SimpleNamespace(name=name, owner=SimpleNamespace(global_name=owner_name, id=owner_id))


class TestBuildGuildWelcomeEmbed:
    def test_title_is_the_guild_name(self):
        embed = presenters.build_guild_welcome_embed(make_guild(name="My Server"), "Ari", 5)
        assert embed.title == "My Server"

    def test_description_mentions_the_bot_name_and_guild_count(self):
        embed = presenters.build_guild_welcome_embed(make_guild(), "Ari", 7)
        assert "Thank you for inviting Ari" in embed.description
        assert "7" in embed.description


class TestBuildGuildJoinAdminNoticeEmbed:
    def test_description_mentions_guild_name_and_owner(self):
        guild = make_guild(name="New Server", owner_name="Someone", owner_id=1234)
        embed = presenters.build_guild_join_admin_notice_embed(guild)
        assert "New Server" in embed.description
        assert "Someone" in embed.description
        assert "1234" in embed.description
