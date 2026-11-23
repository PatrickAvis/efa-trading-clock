"""GB power market time calculations.

Durations are calculated in UTC because UK wall-clock arithmetic breaks on clock-change days,
which have 46 or 50 settlement periods rather than 48.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

UK = ZoneInfo("Europe/London")
HALF_HOUR = timedelta(minutes=30)
GATE_CLOSURE_LEAD = timedelta(hours=1)
EFA_DAY_START_HOUR = 23
EFA_BLOCK_HOURS = 4


@dataclass(frozen=True)
class EfaBlock:
    number: int
    start_hour: int
    end_hour: int

    @property
    def label(self) -> str:
        return f"EFA {self.number} ({self.start_hour:02d}-{self.end_hour:02d})"


@dataclass(frozen=True)
class ClockState:
    now: datetime
    gate_closure: datetime
    seconds_to_gate_closure: int
    delivery_start: datetime
    delivery_end: datetime
    settlement_period: int
    efa_block: EfaBlock

    @property
    def countdown(self) -> str:
        minutes, seconds = divmod(self.seconds_to_gate_closure, 60)
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def title(self) -> str:
        return (
            f"GC: {self.countdown} | P: {self.settlement_period} | "
            f"T: {self.delivery_start:%H:%M} - {self.delivery_end:%H:%M} | {self.efa_block.label}"
        )


def _require_aware(moment: datetime) -> None:
    if moment.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")


def next_gate_closure(now: datetime) -> datetime:
    """Return the next half-hour boundary strictly after ``now``, in UTC."""
    _require_aware(now)
    now_utc = now.astimezone(UTC)
    period_start = now_utc.replace(minute=now_utc.minute // 30 * 30, second=0, microsecond=0)
    return period_start + HALF_HOUR


def settlement_period(start: datetime) -> int:
    """Return the settlement period number for a period starting at ``start``."""
    _require_aware(start)
    local = start.astimezone(UK)
    midnight = datetime(local.year, local.month, local.day, tzinfo=UK)
    return (start.astimezone(UTC) - midnight.astimezone(UTC)) // HALF_HOUR + 1


def efa_block(moment: datetime) -> EfaBlock:
    """Return the EFA block in progress at ``moment``."""
    _require_aware(moment)
    hour = moment.astimezone(UK).hour
    index = (hour - EFA_DAY_START_HOUR) % 24 // EFA_BLOCK_HOURS
    start_hour = (EFA_DAY_START_HOUR + index * EFA_BLOCK_HOURS) % 24
    return EfaBlock(index + 1, start_hour, (start_hour + EFA_BLOCK_HOURS) % 24)


def clock_state(now: datetime | None = None) -> ClockState:
    """Build everything the clock displays for a single moment."""
    now = datetime.now(UTC) if now is None else now
    _require_aware(now)

    gate_closure = next_gate_closure(now)
    delivery_start = gate_closure + GATE_CLOSURE_LEAD
    delivery_end = delivery_start + HALF_HOUR
    whole_second = now.astimezone(UTC).replace(microsecond=0)

    return ClockState(
        now=now.astimezone(UK),
        gate_closure=gate_closure.astimezone(UK),
        seconds_to_gate_closure=int((gate_closure - whole_second).total_seconds()),
        delivery_start=delivery_start.astimezone(UK),
        delivery_end=delivery_end.astimezone(UK),
        settlement_period=settlement_period(delivery_start),
        efa_block=efa_block(now),
    )
