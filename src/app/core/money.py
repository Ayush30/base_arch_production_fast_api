"""Money is an integer in minor units, never a floating-point dollar value."""

from app.core.config import settings
from app.core.exceptions import ValidationError

CURRENCY_EXPONENTS = {"USD": 2, "EUR": 2, "GBP": 2, "JPY": 0, "KWD": 3}


def validate_currency(currency: str) -> str:
    if currency not in settings.supported_currencies:
        raise ValidationError("Currency is not enabled")
    return currency


def commission(amount: int, basis_points: int) -> int:
    # Integer half-up rounding. 100 basis points = 1 percent.
    return (amount * basis_points + 5000) // 10000
