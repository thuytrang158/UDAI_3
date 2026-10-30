"""Currency conversion helpers for user-facing Vietnamese dong amounts."""

# Wise mid-market reference observed on 2026-10-29.
INR_TO_VND_RATE = 271.372


def inr_to_vnd(amount: float | int) -> int:
    """Convert INR to whole VND for display and API output."""
    return round(float(amount) * INR_TO_VND_RATE)


def vnd_to_inr(amount: float | int) -> int:
    """Convert VND to the internal whole-INR accommodation budget."""
    return max(round(float(amount) / INR_TO_VND_RATE), 0)
