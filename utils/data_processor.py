from __future__ import annotations

from typing import Dict, List, Any, Optional, Tuple


def parse_transactions(raw_lines: List[str]) -> List[Dict[str, Any]]:
    """
    Parses raw lines into clean list of dictionaries.

    Requirements:
    - Split by pipe delimiter '|'
    - Handle commas within ProductName (remove)
    - Remove commas from numeric fields and convert to proper types
    - Convert Quantity to int
    - Convert UnitPrice to float
    - Skip rows with incorrect number of fields
    """
    cleaned: List[Dict[str, Any]] = []
    expected_fields = 8

    for line in raw_lines:
        if not line:
            continue

        row = line.strip()
        if row == "":
            continue

        parts = row.split("|")
        if len(parts) != expected_fields:
            continue

        transaction_id = parts[0].strip()
        date = parts[1].strip()
        product_id = parts[2].strip()

        # Remove commas inside ProductName
        product_name = parts[3].strip().replace(",", "")

        # Remove commas inside numeric fields
        qty_str = parts[4].strip().replace(",", "")
        price_str = parts[5].strip().replace(",", "")

        try:
            quantity = int(qty_str)
            unit_price = float(price_str)
        except ValueError:
            continue

        customer_id = parts[6].strip()
        region = parts[7].strip()

        cleaned.append(
            {
                "TransactionID": transaction_id,
                "Date": date,
                "ProductID": product_id,
                "ProductName": product_name,
                "Quantity": quantity,
                "UnitPrice": unit_price,
                "CustomerID": customer_id,
                "Region": region,
            }
        )

    return cleaned


def validate_and_filter(
    transactions: List[Dict[str, Any]],
    region: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
) -> Tuple[List[Dict[str, Any]], int, Dict[str, int]]:
    """
    Validates transactions and applies optional filters.

    Returns: (valid_transactions, invalid_count, filter_summary)

    Validation Rules:
    - Quantity > 0
    - UnitPrice > 0
    - Required fields present
    - TransactionID starts with 'T'
    - ProductID starts with 'P'
    - CustomerID starts with 'C'
    """
    required_fields = [
        "TransactionID", "Date", "ProductID", "ProductName",
        "Quantity", "UnitPrice", "CustomerID", "Region"
    ]

    total_input = len(transactions)
    invalid_count = 0
    valid: List[Dict[str, Any]] = []

    # Validate
    for tx in transactions:
        # Required fields present
        missing = False
        for f in required_fields:
            if f not in tx:
                missing = True
                break
            if isinstance(tx[f], str) and tx[f].strip() == "":
                missing = True
                break
        if missing:
            invalid_count += 1
            continue

        # Numeric checks
        try:
            qty = int(tx["Quantity"])
            price = float(tx["UnitPrice"])
        except (ValueError, TypeError):
            invalid_count += 1
            continue

        if qty <= 0 or price <= 0:
            invalid_count += 1
            continue

        tid = str(tx["TransactionID"]).strip()
        pid = str(tx["ProductID"]).strip()
        cid = str(tx["CustomerID"]).strip()

        if not tid.startswith("T"):
            invalid_count += 1
            continue
        if not pid.startswith("P"):
            invalid_count += 1
            continue
        if not cid.startswith("C"):
            invalid_count += 1
            continue

        # Keep
        tx_clean = dict(tx)
        tx_clean["Quantity"] = qty
        tx_clean["UnitPrice"] = price
        valid.append(tx_clean)

    # Apply region filter (optional)
    filtered_by_region = 0
    after_region = valid
    if region is not None and str(region).strip() != "":
        target = str(region).strip().lower()
        before = len(after_region)
        after_region = [t for t in after_region if str(t["Region"]).strip().lower() == target]
        filtered_by_region = before - len(after_region)

    # Apply amount filter (optional)
    filtered_by_amount = 0
    after_amount = after_region
    if min_amount is not None or max_amount is not None:
        before = len(after_amount)

        def in_range(t: Dict[str, Any]) -> bool:
            amt = t["Quantity"] * t["UnitPrice"]
            if min_amount is not None and amt < float(min_amount):
                return False
            if max_amount is not None and amt > float(max_amount):
                return False
            return True

        after_amount = [t for t in after_amount if in_range(t)]
        filtered_by_amount = before - len(after_amount)

    summary = {
        "total_input": total_input,
        "invalid": invalid_count,
        "filtered_by_region": filtered_by_region,
        "filtered_by_amount": filtered_by_amount,
        "final_count": len(after_amount),
    }

    return after_amount, invalid_count, summary