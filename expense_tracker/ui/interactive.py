from pathlib import Path
from typing import List

from expense_tracker.config import DEFAULT_CSV
from expense_tracker.models.transaction import Transaction
from expense_tracker.exceptions import ValidationError, StorageError, OperationCancelled
from expense_tracker.utils import parse_date_ymd, parse_amount, confirm, pretty_print_table
from expense_tracker.storage import StorageManager
from expense_tracker.reporting import ReportGenerator


CANCEL_KEYWORDS = {"q", "quit", "cancel"}


def _check_cancel(raw: str):
    if raw is None:
        return
    if raw.strip().lower() in CANCEL_KEYWORDS:
        raise OperationCancelled()


class CLIApp:
    def __init__(self, storage_manager: StorageManager, report_generator: ReportGenerator):
        self.store = storage_manager
        self.reports = report_generator

    # Prompt helpers (immediate validation + cancel)
    def _prompt_date(self, prompt_text: str, allow_empty: bool = False, default: str | None = None) -> str | None:
        while True:
            raw = input(prompt_text).strip()
            if raw == "" and allow_empty:
                return None
            if raw == "" and default is not None:
                return default
            _check_cancel(raw)
            try:
                parse_date_ymd(raw)
                return raw
            except ValidationError as e:
                print(f"Invalid date: {e}. Please enter YYYYMMDD or 'q' to cancel.")

    def _prompt_amount(self, prompt_text: str, allow_empty: bool = False, default: str | None = None) -> str | None:
        while True:
            raw = input(prompt_text).strip()
            if raw == "" and allow_empty:
                return None
            if raw == "" and default is not None:
                return default
            _check_cancel(raw)
            try:
                parse_amount(raw)
                return raw
            except ValidationError as e:
                print(f"Invalid amount: {e}. Enter a number like 12.50 or 'q' to cancel.")

    def _prompt_nonempty(self, prompt_text: str, allow_empty: bool = False, default: str | None = None) -> str | None:
        while True:
            raw = input(prompt_text).strip()
            if raw == "" and allow_empty:
                return None
            if raw == "" and default is not None:
                return default
            _check_cancel(raw)
            if raw == "":
                print("This field is required; please enter a value or 'q' to cancel.")
                continue
            return raw

    def _prompt_path(self, prompt_text: str, allow_empty: bool = False) -> str | None:
        while True:
            raw = input(prompt_text).strip()
            if raw == "" and allow_empty:
                return None
            _check_cancel(raw)
            if raw == "":
                print("Please enter a path or 'q' to cancel.")
                continue
            return raw

    # UI actions
    def add_transaction(self):
        print("\nAdd Transaction (type 'q' to cancel at any prompt)")
        try:
            date_str = self._prompt_date("Date (YYYYMMDD): ")
            amount_str = self._prompt_amount("Amount (use dot, e.g. 12.50): ")
            category = self._prompt_nonempty("Category: ")
            description = input("Description (optional): ").strip()
            _check_cancel(description)
            tx = Transaction.from_input(date_str, amount_str, category, description)
            self.store.append(tx)
            print(f"Transaction added with id {tx.id}")
        except OperationCancelled:
            print("Add cancelled. Returning to main menu.")
        except ValidationError as e:
            print(f"Invalid input: {e}")
        except StorageError as e:
            print(f"Storage error: {e}")

    def list_transactions(self):
        print("\nList Transactions (type 'q' to cancel filters)")
        txs = self.store.load()
        if not txs:
            print("No transactions found.")
            return
        try:
            start = self._prompt_date("Start date (YYYYMMDD) or Enter to skip: ", allow_empty=True)
            end = self._prompt_date("End date (YYYYMMDD) or Enter to skip: ", allow_empty=True)
            category = self._prompt_nonempty("Filter category or Enter to skip: ", allow_empty=True)
        except OperationCancelled:
            print("Listing cancelled. Returning to main menu.")
            return

        start_date = parse_date_ymd(start) if start else None
        end_date = parse_date_ymd(end) if end else None

        filtered: List[Transaction] = []
        for tx in txs:
            if start_date and tx.date < start_date:
                continue
            if end_date and tx.date > end_date:
                continue
            if category and tx.category.lower() != category.lower():
                continue
            filtered.append(tx)

        rows = [
            [str(i + 1), tx.id, tx.date.strftime("%Y%m%d"), f"{tx.amount}", tx.category, tx.description or ""]
            for i, tx in enumerate(filtered)
        ]
        headers = ["#", "id", "date", "amount", "category", "description"]
        pretty_print_table(rows, headers)

    def _select_transaction_loop(self, txs: List[Transaction]):
        if not txs:
            print("No transactions available.")
            return None, None
        headers = ["#", "id", "date", "amount", "category"]
        while True:
            rows = [[str(i + 1), tx.id, tx.date.strftime("%Y%m%d"), f"{tx.amount}", tx.category] for i, tx in enumerate(txs)]
            pretty_print_table(rows, headers)
            choice = input("Choose by number or enter transaction id (or 'q' to cancel): ").strip()
            if not choice:
                print("No selection made. Enter a number, an id, or 'q' to cancel.")
                continue
            if choice.lower() in CANCEL_KEYWORDS:
                print("Selection cancelled.")
                return None, None
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(txs):
                    return idx, txs[idx]
                else:
                    print("Number out of range; try again or 'q' to cancel.")
                    continue
            except ValueError:
                pass
            for i, tx in enumerate(txs):
                if tx.id == choice:
                    return i, tx
            print("Selection not found; try again or 'q' to cancel.")

    def edit_transaction(self):
        print("\nEdit Transaction (type 'q' to cancel at any prompt)")
        txs = self.store.load()
        if not txs:
            print("No transactions to edit.")
            return
        idx, tx = self._select_transaction_loop(txs)
        if tx is None:
            return
        print("Press Enter to leave a field unchanged. Type 'q' to cancel.")

        try:
            date_prompt = f"Date ({tx.date.strftime('%Y%m%d')}): "
            date_input = self._prompt_date(date_prompt, allow_empty=True)
            date_str = tx.date.strftime("%Y%m%d") if date_input is None else date_input

            amount_prompt = f"Amount ({tx.amount}): "
            amount_input = self._prompt_amount(amount_prompt, allow_empty=True)
            amount_str = f"{tx.amount}" if amount_input is None else amount_input

            category_prompt = f"Category ({tx.category}): "
            while True:
                raw = input(category_prompt).strip()
                if raw.lower() in CANCEL_KEYWORDS:
                    raise OperationCancelled()
                if raw == "":
                    category = tx.category
                    break
                category = raw
                break

            desc_prompt = f"Description ({tx.description}): "
            raw_desc = input(desc_prompt).strip()
            _check_cancel(raw_desc)
            description = raw_desc if raw_desc != "" else tx.description

            new_tx = Transaction.from_input(date_str, amount_str, category, description, id=tx.id)
            txs[idx] = new_tx
            self.store.save(txs)
            print("Transaction updated.")
        except OperationCancelled:
            print("Edit cancelled. Returning to main menu.")
        except ValidationError as e:
            print(f"Invalid input: {e}")
        except StorageError as e:
            print(f"Storage error: {e}")

    def delete_transaction(self):
        print("\nDelete Transaction (type 'q' to cancel)")
        txs = self.store.load()
        if not txs:
            print("No transactions to delete.")
            return
        idx, tx = self._select_transaction_loop(txs)
        if tx is None:
            return
        confirmed = confirm(f"Delete transaction {tx.id} of {tx.amount} on {tx.date.strftime('%Y%m%d')}? (y/n): ")
        if not confirmed:
            print("Delete cancelled.")
            return
        try:
            del txs[idx]
            self.store.save(txs)
            print("Transaction deleted.")
        except StorageError as e:
            print(f"Storage error: {e}")

    def reports_menu(self):
        while True:
            print("\nReports Menu")
            print("1) Monthly totals (YYYYMM)")
            print("2) Category totals (date range)")
            print("3) Export an aggregated report to CSV")
            print("4) Back to main menu")
            choice = input("Choose: ").strip()
            txs = self.store.load()

            if choice == "1":
                agg = self.reports.aggregate_by_month(txs)
                rows = [[month, f"{total}"] for month, total in sorted(agg.items())]
                pretty_print_table(rows, ["month", "total"])

            elif choice == "2":
                try:
                    start = self._prompt_date("Start date (YYYYMMDD) or Enter to skip: ", allow_empty=True)
                    end = self._prompt_date("End date (YYYYMMDD) or Enter to skip: ", allow_empty=True)
                except OperationCancelled:
                    print("Report date entry cancelled. Returning to Reports menu.")
                    continue
                s = parse_date_ymd(start) if start else None
                e = parse_date_ymd(end) if end else None
                agg = self.reports.aggregate_by_category(txs, s, e)
                rows = [[cat, f"{total}"] for cat, total in sorted(agg.items(), key=lambda x: -abs(x[1]))]
                pretty_print_table(rows, ["category", "total"])

            elif choice == "3":
                print("Export an aggregated report to CSV (type 'q' to cancel any prompt)")
                opt = input("choose a) monthly totals  b) category totals  (a/b): ").strip().lower()
                if opt.lower() in CANCEL_KEYWORDS:
                    print("Export cancelled.")
                    continue
                if opt == "a":
                    agg = self.reports.aggregate_by_month(txs)
                    rows = [[m, f"{t}"] for m, t in sorted(agg.items())]
                    try:
                        path_str = self._prompt_path("Export file path (e.g. reports/monthly.csv): ")
                    except OperationCancelled:
                        print("Export cancelled.")
                        continue
                    try:
                        self.reports.export_report_csv(Path(path_str), rows, ["month", "total"])
                        print(f"Exported to {path_str}")
                    except StorageError as e:
                        print(f"Export failed: {e}")

                elif opt == "b":
                    try:
                        start = self._prompt_date("Start date (YYYYMMDD): ")
                        end = self._prompt_date("End date (YYYYMMDD): ")
                        path_str = self._prompt_path("Export file path (e.g. reports/by_category.csv): ")
                    except OperationCancelled:
                        print("Export cancelled.")
                        continue
                    s = parse_date_ymd(start)
                    e = parse_date_ymd(end)
                    agg = self.reports.aggregate_by_category(txs, s, e)
                    rows = [[c, f"{t}"] for c, t in sorted(agg.items(), key=lambda x: -abs(x[1]))]
                    try:
                        self.reports.export_report_csv(Path(path_str), rows, ["category", "total"])
                        print(f"Exported to {path_str}")
                    except StorageError as e:
                        print(f"Export failed: {e}")
                else:
                    print("Invalid option. Enter 'a' or 'b' or 'q' to cancel.")

            elif choice == "4":
                return
            else:
                print("Invalid choice.")

    def run(self):
        while True:
            print("\nPersonal Expense Tracker")
            print("1) Add transaction")
            print("2) List transactions")
            print("3) Edit transaction")
            print("4) Delete transaction")
            print("5) Reports")
            print("6) Exit")
            choice = input("Choose: ").strip()
            if choice == "1":
                self.add_transaction()
            elif choice == "2":
                self.list_transactions()
            elif choice == "3":
                self.edit_transaction()
            elif choice == "4":
                self.delete_transaction()
            elif choice == "5":
                self.reports_menu()
            elif choice == "6":
                print("Have a Good Day.")
                break
            else:
                print("Invalid choice. Enter a number 1-6.")
