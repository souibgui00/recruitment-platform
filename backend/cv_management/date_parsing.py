from datetime import date, datetime
from dateutil import parser as date_parser


def parse_flexible_date(raw_date: str | None) -> date | None:
    if not raw_date:
        return None

    if raw_date.strip().lower() in ("present", "now", "actuel", "aujourd'hui"):
        return None

    try:
        parsed = date_parser.parse(raw_date, default=datetime(2000, 1, 1))
        return parsed.date()
    except (ValueError, OverflowError):
        return None