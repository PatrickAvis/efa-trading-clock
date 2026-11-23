"""Countdown background colours."""

LAST_MINUTE_STEP = 29
MIDPOINT_STEP = 15
FADE_STEPS = 14


def countdown_colour(seconds_remaining: int) -> tuple[int, int, int]:
    """Fade from green at 30 minutes, through yellow at 15, to red in the final minute."""
    minute = min(max(seconds_remaining, 0) // 60, LAST_MINUTE_STEP)
    if minute < MIDPOINT_STEP:
        return 255, round(255 * minute / FADE_STEPS), 0
    return round(255 * (LAST_MINUTE_STEP - minute) / FADE_STEPS), 255, 0
