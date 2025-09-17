from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_CSV = DEFAULT_DATA_DIR / "transactions.csv"
ENCODING = "utf-8"
CSV_HEADER = ["id", "date", "amount", "category", "description"]
