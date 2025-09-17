from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import uuid

from expense_tracker.exceptions import ValidationError


@dataclass
class Transaction:
    id: str
    date: date
    amount: Decimal
    category: str
    description: str = ""

    @classmethod
    def from_input(cls, date_str: str, amount_str: str, category: str, description: str = "", id: str | None = None):
        if not date_str:
            raise ValidationError("date is required")
        try:
            d = datetime.strptime(date_str, "%Y%m%d").date()
        except Exception:
            raise ValidationError(f"invalid date '{date_str}': expected YYYYMMDD")

        if not amount_str:
            raise ValidationError("amount is required")
        try:
            amt = Decimal(amount_str)
        except (InvalidOperation, ValueError):
            raise ValidationError(f"invalid amount '{amount_str}': expected decimal with dot as separator")

        if not category:
            raise ValidationError("category is required")

        tx_id = id if id else str(uuid.uuid4())
        return cls(id=tx_id, date=d, amount=amt, category=category.strip(), description=description.strip() if description else "")

    def to_csv_row(self) -> dict:
        return {
            "id": self.id,
            "date": self.date.strftime("%Y%m%d"),
            "amount": f"{self.amount}",
            "category": self.category,
            "description": self.description or "",
        }

    @classmethod
    def from_csv_row(cls, row: dict):
        try:
            tx_id = row.get("id") or ""
            date_s = row.get("date")
            amount_s = row.get("amount")
            category = row.get("category") or ""
            description = row.get("description") or ""
            if not tx_id:
                raise ValidationError("missing id in CSV row")
            if not date_s:
                raise ValidationError("missing date in CSV row")
            if not amount_s:
                raise ValidationError("missing amount in CSV row")
            d = datetime.strptime(date_s, "%Y%m%d").date()
            a = Decimal(amount_s)
            return cls(id=tx_id, date=d, amount=a, category=category, description=description)
        except ValidationError:
            raise
        except Exception as ex:
            raise ValidationError(f"invalid CSV row: {ex}")
