from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import List

from expense_tracker.exceptions import ValidationError


def parse_date_ymd(s: str) -> date:
    if not s:
        raise ValidationError("date string empty")
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except Exception:
        raise ValidationError(f"invalid date '{s}': expected YYYYMMDD")


def parse_amount(s: str) -> Decimal:
    if not s:
        raise ValidationError("amount string empty")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        raise ValidationError(f"invalid amount '{s}': expected decimal using dot as separator")


def confirm(prompt: str) -> bool:
    ans = input(prompt).strip().lower()
    return ans in ("y", "yes")


def pretty_print_table(rows: List[list], headers: List[str]) -> None:
    # compute widths
    if not rows:
        print("No rows.")
        return
    cols = list(zip(*([headers] + rows)))
    widths = [max(len(str(x)) for x in col) for col in cols]
    header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, widths))
    sep_line = "-+-".join("-" * w for w in widths)
    print(header_line)
    print(sep_line)
    for row in rows:
        print(" | ".join(str(c).ljust(w) for c, w in zip(row, widths)))
