from pathlib import Path
import logging

from expense_tracker.config import DEFAULT_CSV
from expense_tracker.storage import StorageManager
from expense_tracker.reporting import ReportGenerator
from expense_tracker.ui import CLIApp

LOG = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    LOG.info("Starting Expense Tracker")
    # Allow user to override default path at startup
    csv_path_input = input(f"Data file [{DEFAULT_CSV}] (Press Enter to accept): ").strip()
    csv_path = Path(csv_path_input) if csv_path_input else DEFAULT_CSV
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    store = StorageManager(csv_path)
    reports = ReportGenerator()
    app = CLIApp(store, reports)
    app.run()


if __name__ == "__main__":
    main()
