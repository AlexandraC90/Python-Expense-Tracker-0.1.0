import csv
import os
import tempfile
from pathlib import Path
from typing import List

from config import ENCODING, CSV_HEADER
from transaction import Transaction
from exceptions import StorageError, ValidationError


def _ensure_parent(path: Path):
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


def load_transactions(path: Path) -> List[Transaction]:
    path = Path(path)
    if not path.exists():
        return []
    txs = []
    try:
        with path.open("r", encoding=ENCODING, newline="") as fh:
            reader = csv.DictReader(fh)
            # If file empty or missing header, return []
            if reader.fieldnames is None:
                return []
            for row in reader:
                try:
                    tx = Transaction.from_csv_row(row)
                    txs.append(tx)
                except ValidationError as e:
                    # skip bad rows but continue
                    # logging locally to stderr via print to keep dependency minimal
                    print(f"Warning: skipping invalid row: {e}")
                    continue
    except Exception as ex:
        raise StorageError(f"could not read {path}: {ex}")
    return txs


def save_transactions(path: Path, transactions: List[Transaction]):
    path = Path(path)
    _ensure_parent(path)
    dirpath = path.parent
    try:
        # create a temporary file in same directory for atomic replace
        with tempfile.NamedTemporaryFile("w", encoding=ENCODING, delete=False, dir=str(dirpath), newline="") as tmp:
            writer = csv.DictWriter(tmp, fieldnames=CSV_HEADER)
            writer.writeheader()
            for tx in transactions:
                writer.writerow(tx.to_csv_row())
            tmp_name = tmp.name
        # atomic replace
        os.replace(tmp_name, str(path))
    except Exception as ex:
        raise StorageError(f"could not write to {path}: {ex}")


def append_transaction(path: Path, transaction: Transaction):
    path = Path(path)
    _ensure_parent(path)
    # if file doesn't exist, create with header
    txs = []
    if path.exists():
        txs = load_transactions(path)
    txs.append(transaction)
    save_transactions(path, txs)
