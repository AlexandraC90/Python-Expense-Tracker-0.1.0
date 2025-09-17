import csv
import os
import tempfile
from pathlib import Path
from typing import List

from expense_tracker.config import ENCODING, CSV_HEADER
from expense_tracker.models.transaction import Transaction
from expense_tracker.exceptions import StorageError, ValidationError


class StorageManager:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._ensure_parent()

    def _ensure_parent(self):
        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> List[Transaction]:
        if not self.path.exists():
            return []
        txs: List[Transaction] = []
        try:
            with self.path.open("r", encoding=ENCODING, newline="") as fh:
                reader = csv.DictReader(fh)
                if reader.fieldnames is None:
                    return []
                for row in reader:
                    try:
                        tx = Transaction.from_csv_row(row)
                        txs.append(tx)
                    except ValidationError as e:
                        print(f"Warning: skipping invalid row: {e}")
                        continue
        except Exception as ex:
            raise StorageError(f"could not read {self.path}: {ex}")
        return txs

    def save(self, transactions: List[Transaction]):
        self._ensure_parent()
        dirpath = self.path.parent
        try:
            with tempfile.NamedTemporaryFile("w", encoding=ENCODING, delete=False, dir=str(dirpath), newline="") as tmp:
                writer = csv.DictWriter(tmp, fieldnames=CSV_HEADER)
                writer.writeheader()
                for tx in transactions:
                    writer.writerow(tx.to_csv_row())
                tmp_name = tmp.name
            os.replace(tmp_name, str(self.path))
        except Exception as ex:
            raise StorageError(f"could not write to {self.path}: {ex}")

    def append(self, transaction: Transaction):
        txs = []
        if self.path.exists():
            txs = self.load()
        txs.append(transaction)
        self.save(txs)
