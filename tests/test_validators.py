import pytest
from bot.utils.datetime_helpers import is_valid_date, is_valid_time


@pytest.mark.parametrize("value", ["2025-01-01", "2025-12-31", "2000-06-15"])
def test_valid_dates(value: str):
    assert is_valid_date(value) is True


@pytest.mark.parametrize("value", ["2025-13-01", "25-01-01", "2025/01/01", "", "abc"])
def test_invalid_dates(value: str):
    assert is_valid_date(value) is False


@pytest.mark.parametrize("value", ["00:00", "23:59", "12:30", "09:45"])
def test_valid_times(value: str):
    assert is_valid_time(value) is True


@pytest.mark.parametrize("value", ["24:00", "12:60", "1:5", "", "ab:cd"])
def test_invalid_times(value: str):
    assert is_valid_time(value) is False
