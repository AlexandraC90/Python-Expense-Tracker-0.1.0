# Python-Expense-Tracker-0.1.0
A small command-line Python program to record, list, edit, delete and report personal transactions.

This project demonstrates object-oriented design (a `Transaction` model), modular package layout, safe CSV persistence (atomic writes) and defensive input validation.

---

## Quick facts
- Language: Python (3.10+ recommended)
- Dependencies: **none** (uses Python standard library). Optional: `tabulate` for nicer tables (see below).
- To launch, download as Zip and extract
- Launch terminal from inside the extracted folder (this is the Root Directory)
- Entry point: `python -m expense_tracker.app` from the Root directory

---

## What it does
- Add transactions (date `YYYYMMDD`, decimal amount, category, optional description)
- List transactions with simple filters (date range, category)
- Edit or delete a transaction by index or id
- Monthly and category aggregation reports, with CSV export option
- Safe CSV persistence using temp-file + atomic replace to avoid partial writes

---

## Prerequisites
- Python 3.10 or newer installed
- (Optional) Create a virtual environment for isolation

---

## Install & run (recommended)
```bash
# create & activate venv (macOS / Linux)
python -m venv .venv
source .venv/bin/activate

# on Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

# install optional helper (if you want pretty tables)
pip install tabulate

# run the app
python -m expense_tracker.app
