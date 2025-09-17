from collections import defaultdict
from decimal import Decimal
from datetime import date
from pathlib import Path
import csv
import os
import tempfile

from transaction import Transaction
from exceptions import StorageError
from config import ENCODING


def aggregate_by_month(transactions: list[Transaction]) -> dict:
    res: dict[str, Decimal] = {}
    agg = defaultdict(Decimal)
    for tx in transactions:
        key = tx.date.strftime("%Y%m")
        agg[key] += tx.amount
    for k, v in agg.items():
        res[k] = v
    return res


def aggregate_by_category(transactions: list[Transaction], start: date | None = None, end: date | None = None) -> dict:
    agg = defaultdict(Decimal)
    for tx in transactions:
        if start and tx.date < start:
            continue
        if end and tx.date > end:
            continue
        agg[tx.category] += tx.amount
    return dict(agg)


def export_report_csv(path: Path, rows: list[list], headers: list[str]):
    path = Path(path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    dirpath = path.parent
    try:
        with tempfile.NamedTemporaryFile("w", encoding=ENCONDING if False else "utf-8", delete=False, dir=str(dirpath), newline="") as tmp:
            writer = csv.writer(tmp)
            writer.writerow(headers)
            for r in rows:
                writer.writerow(r)
            tmp_name = tmp.name
        os.replace(tmp_name, str(path))
    except Exception as ex:
        raise StorageError(f"could not export report to {path}: {ex}")
