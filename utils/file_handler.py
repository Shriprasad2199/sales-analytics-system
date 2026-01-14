from __future__ import annotations

from pathlib import Path
from typing import List


def read_sales_data(filename: str) -> List[str]:
    """
    Reads sales data from file handling encoding issues.

    Returns: list of raw lines (strings)
    Expected: ['T001|2024-12-01|P101|Laptop|2|45000|C001|North', ...]

    Requirements:
    - Use 'with' statement
    - Handle different encodings (try 'utf-8', 'latin-1', 'cp1252')
    - Handle FileNotFoundError with appropriate error message
    - Skip the header row
    - Remove empty lines
    """
    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(f"Sales data file not found: {path.resolve()}")

    encodings_to_try = ["utf-8", "latin-1", "cp1252"]
    last_error = None

    for enc in encodings_to_try:
        try:
            with path.open("r", encoding=enc) as f:
                lines = f.read().splitlines()

            # Remove empty lines
            lines = [ln.strip() for ln in lines if ln and ln.strip()]

            # Skip header if present
            if lines and lines[0].lower().startswith(
                "transactionid|date|productid|productname|quantity|unitprice|customerid|region"
            ):
                lines = lines[1:]

            return lines

        except UnicodeDecodeError as e:
            last_error = e
            continue

    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Unable to decode file. Last error: {last_error}")