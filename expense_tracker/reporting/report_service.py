from collections import defaultdict
from decimal import Decimal
from datetime import date
from pathlib import Path
import csv
import os
import tempfile

from expense_tracker.models.transaction import Transaction
from expense_tracker.exceptions import StorageError
from expense_tracker.config import ENCODING


class ReportGenerator:
    def aggregate_by_month(self, transactions: list[Transaction]) -> dict[str, Decimal]:
        agg: dict[str, Decimal] = {}
        temp = defaultdict(Decimal)
        for tx in transactions:
            key = tx.date.strftime("%Y%m")
            temp[key] += tx.amount
        for k, v in temp.items():
            agg[k] = v
        return agg

    def aggregate_by_category(self, transactions: list[Transaction], start: date | None = None, end: date | None = None) -> dict[str, Decimal]:
        temp = defaultdict(Decimal)
        for tx in transactions:
            if start and tx.date < start:
                continue
            if end and tx.date > end:
                continue
            temp[tx.category] += tx.amount
        return dict(temp)

    def export_report_csv(self, path: Path, rows: list[list], headers: list[str]):
        path = Path(path)
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        dirpath = path.parent
        try:
            with tempfile.NamedTemporaryFile("w", encoding=ENCODING, delete=False, dir=str(dirpath), newline="") as tmp:
                writer = csv.writer(tmp)
                writer.writerow(headers)
                for r in rows:
                    writer.writerow(r)
                tmp_name = tmp.name
            os.replace(tmp_name, str(path))
        except Exception as ex:
            raise StorageError(f"could not export report to {path}: {ex}")
