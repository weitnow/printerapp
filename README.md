# Excel → SQLite Printer Import Script

This project imports printer, slot, bureau, and CARIdoc data from an Excel file into a structured SQLite database.

The script:
- Reads an Excel file (`.xlsx`)
- Normalizes the data into multiple relational tables
- Drops existing tables and recreates them
- Imports all data in one run

---

## Requirements

- **Python 3.9+** (recommended)
- Python packages:
  - `pandas`
  - `openpyxl`

All other used modules (e.g. `sqlite3`) are part of the Python standard library.

---

## Installation

### 1. Clone or copy the project

Make sure the following files are in the same directory:

- `import_printers.py` (your script)
- `requirements.txt`
- `Druckerliste_CARI.xlsx`

---

### 2. (Recommended) Create a virtual environment

#### Windows
```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Linux / macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Excel File Expectations

The Excel file **`Druckerliste_CARI.xlsx`** must:

- Be located in the same directory as the script (or adjust the path)
- Contain **at least one sheet** (currently only the first sheet is read)
- Include the following columns:

Required columns:
- `Standort`
- `Fachabteilung`
- `Drucker Modell`
- `Druckername`
- `Schacht Name`
- `Format`
- `2-sided`
- `Inspect`
- `CARIdoc`
- `Bureau`
- `Bureau-ID`
- `Bemerkung`

⚠️ Column names must match **exactly**.

---

## Database Output

The script creates (or overwrites) the SQLite database:

```
printers.db
```

Tables created:
- `lieugestion`
- `fachabteilung`
- `printermodels`
- `printernames`
- `printerslots`
- `bureaus`
- `slot_caridocs`

Existing tables with these names are **dropped before import**.

---

## Running the Script

```bash
python import_printers.py
```

If successful, you will see:

```
Drop Table and Import completed successfully!
```

---

## Notes & Customization

- **Sheet selection**
  - Currently the script reads the **first Excel sheet** (`sheet_name = 0`)
  - You can change this to another index or a sheet name if needed

- **Re-running the script**
  - Safe to re-run: all relevant tables are dropped and recreated

- **SQLite inspection**
  - You can inspect `printers.db` using tools like:
    - DB Browser for SQLite
    - SQLiteStudio
    - `sqlite3 printers.db` (CLI)

---

## Troubleshooting

**Error: missing openpyxl**
```text
ImportError: Missing optional dependency 'openpyxl'
```
➡ Run:
```bash
pip install openpyxl
```

**Excel file not found**
➡ Check the filename and path in:
```python
xlsx_file = "Druckerliste_CARI.xlsx"
```

---

## License / Internal Use

This script is intended for internal data import and maintenance purposes.
Adjust and extend as needed for your environment.

