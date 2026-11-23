from datetime import UTC, date, datetime, timedelta

import pytest

from efa_trading_clock.periods import (
    HALF_HOUR,
    UK,
    clock_state,
    efa_block,
    next_gate_closure,
    settlement_period,
)


def uk(year, month, day, hour, minute=0, second=0, microsecond=0, fold=0):
    return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=UK, fold=fold)


def test_mid_period_state():
    state = clock_state(uk(2026, 6, 15, 10, 10, 10))
    assert state.gate_closure == uk(2026, 6, 15, 10, 30)
    assert state.countdown == "19:50"
    assert state.delivery_start == uk(2026, 6, 15, 11, 30)
    assert state.delivery_end == uk(2026, 6, 15, 12, 0)
    assert state.settlement_period == 24
    assert state.title == "GC: 19:50 | P: 24 | T: 11:30 - 12:00 | EFA 3 (07-11)"


def test_exact_boundary_moves_to_next_gate_closure():
    state = clock_state(uk(2026, 6, 15, 10, 30))
    assert state.gate_closure == uk(2026, 6, 15, 11, 0)
    assert state.countdown == "30:00"
    assert state.settlement_period == 25


def test_last_second_before_gate_closure():
    state = clock_state(uk(2026, 6, 15, 10, 29, 59, 999_999))
    assert state.gate_closure == uk(2026, 6, 15, 10, 30)
    assert state.countdown == "00:01"


def test_countdown_across_midnight():
    state = clock_state(uk(2026, 6, 15, 23, 45))
    assert state.gate_closure == uk(2026, 6, 16, 0, 0)
    assert state.countdown == "15:00"
    assert state.delivery_start == uk(2026, 6, 16, 1, 0)
    assert state.settlement_period == 3


def test_year_end_rollover():
    state = clock_state(uk(2026, 12, 31, 22, 45))
    assert state.delivery_start == uk(2027, 1, 1, 0, 0)
    assert state.settlement_period == 1


@pytest.mark.parametrize(
    ("day", "expected_periods"),
    [(date(2026, 6, 15), 48), (date(2026, 3, 29), 46), (date(2026, 10, 25), 50)],
)
def test_periods_in_a_day(day, expected_periods):
    start = datetime(day.year, day.month, day.day, tzinfo=UK).astimezone(UTC)
    next_day = day + timedelta(days=1)
    end = datetime(next_day.year, next_day.month, next_day.day, tzinfo=UK).astimezone(UTC)

    periods = []
    while start < end:
        periods.append(settlement_period(start))
        start += HALF_HOUR

    assert periods == list(range(1, expected_periods + 1))


def test_spring_clock_change_period():
    assert settlement_period(uk(2026, 3, 29, 3, 30)) == 6


def test_autumn_repeated_hour_has_distinct_periods():
    assert settlement_period(uk(2026, 10, 25, 1, 0, fold=0)) == 3
    assert settlement_period(uk(2026, 10, 25, 1, 0, fold=1)) == 5
    assert settlement_period(uk(2026, 10, 25, 2, 0)) == 7


def test_delivery_is_thirty_minutes_across_clock_changes():
    for moment in (uk(2026, 3, 29, 0, 10), uk(2026, 10, 25, 0, 10)):
        state = clock_state(moment)
        assert state.delivery_end.astimezone(UTC) - state.delivery_start.astimezone(UTC) == (
            HALF_HOUR
        )


def test_result_does_not_depend_on_input_timezone():
    moment = uk(2026, 6, 15, 10, 10, 10)
    assert clock_state(moment) == clock_state(moment.astimezone(UTC))


@pytest.mark.parametrize(
    ("hour", "number", "start", "end"),
    [
        (23, 1, 23, 3),
        (0, 1, 23, 3),
        (2, 1, 23, 3),
        (3, 2, 3, 7),
        (6, 2, 3, 7),
        (7, 3, 7, 11),
        (10, 3, 7, 11),
        (11, 4, 11, 15),
        (14, 4, 11, 15),
        (15, 5, 15, 19),
        (18, 5, 15, 19),
        (19, 6, 19, 23),
        (22, 6, 19, 23),
    ],
)
def test_efa_block_edges(hour, number, start, end):
    block = efa_block(uk(2026, 6, 15, hour, 59))
    assert (block.number, block.start_hour, block.end_hour) == (number, start, end)


def test_efa_label():
    assert efa_block(uk(2026, 6, 15, 23)).label == "EFA 1 (23-03)"


@pytest.mark.parametrize("function", [next_gate_closure, settlement_period, efa_block, clock_state])
def test_naive_datetimes_are_rejected(function):
    with pytest.raises(ValueError, match="timezone-aware"):
        function(datetime(2026, 6, 15, 10, 0))
