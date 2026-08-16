import datetime

from core.utils.chat_formatting import humanize_list, humanize_timedelta


class TestHumanizeList:
    def test_empty(self):
        assert humanize_list([]) == ""

    def test_single_item(self):
        assert humanize_list(["One"]) == "One"

    def test_two_items(self):
        assert humanize_list(["One", "Two"]) == "One and Two"

    def test_three_or_more_items(self):
        assert humanize_list(["One", "Two", "Three"]) == "One, Two, and Three"


class TestHumanizeTimedelta:
    def test_from_seconds(self):
        assert humanize_timedelta(seconds=314) == "5 minutes and 14 seconds"

    def test_from_timedelta_with_maximum_units(self):
        result = humanize_timedelta(timedelta=datetime.timedelta(minutes=3.14), maximum_units=1)
        assert result == "3 minutes"

    def test_singular_unit(self):
        assert humanize_timedelta(seconds=1) == "1 second"

    def test_negative_seconds_uses_default_format(self):
        assert humanize_timedelta(seconds=-5) == "negative 5 seconds"

    def test_negative_seconds_with_custom_format(self):
        result = humanize_timedelta(seconds=-5, negative_format="%s ago")
        assert result == "5 seconds ago"

    def test_raises_without_seconds_or_timedelta(self):
        try:
            humanize_timedelta()
            assert False, "expected ValueError"
        except ValueError:
            pass
