import pytest

from efa_trading_clock.colours import countdown_colour


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (1800, (0, 255, 0)),
        (1799, (0, 255, 0)),
        (900, (255, 255, 0)),
        (899, (255, 255, 0)),
        (59, (255, 0, 0)),
        (1, (255, 0, 0)),
        (0, (255, 0, 0)),
    ],
)
def test_countdown_colour(seconds, expected):
    assert countdown_colour(seconds) == expected


def test_every_second_has_a_valid_colour():
    for seconds in range(0, 1801):
        assert all(0 <= channel <= 255 for channel in countdown_colour(seconds))
