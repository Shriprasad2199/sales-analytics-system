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

def calculate_total_revenue(transactions):
    """
    Calculates total revenue from all transactions.
    
    Returns: float (total revenue)
    
    Expected Output: sum of (Quantity * UnitPrice)
    """
    total_revenue = 0.0
    for tx in transactions:
        try:
            quantity = int(tx.get("Quantity", 0))
            unit_price = float(tx.get("UnitPrice", 0.0))
            total_revenue += quantity * unit_price
        except (ValueError, TypeError):
            continue
    return total_revenue

def region_wise_sales(transactions):
    """
    Analyzes sales by region.
    
    Returns: dictionary with region statistics sorted by total_sales descending.
    """
    region_stats = {}
    grand_total = 0.0
    
    for tx in transactions:
        try:
            region = tx.get("Region")
            quantity = int(tx.get("Quantity", 0))
            unit_price = float(tx.get("UnitPrice", 0.0))
            amount = quantity * unit_price
        except (ValueError, TypeError):
            continue
        
        if region not in region_stats: 
            region_stats[region] = {"total_sales": 0.0, "transaction_count": 0}
        
        region_stats[region]["total_sales"] += amount
        region_stats[region]["transaction_count"] += 1
        grand_total += amount
        
    for region in region_stats:
        if grand_total > 0:
            region_stats[region]["percentage"]= round(
                (region_stats[region]["total_sales"]/ grand_total) *100,2
            )
        else:
            region_stats[region]["percentage"] = 0.0
    
    sorted_region_stats = dict(
        sorted(region_stats.items(), key=lambda item: item[1]["total_sales"], reverse=True)
    )
    
    return sorted_region_stats


def top_selling_products(transactions, n =5):
    """
    Finds top n products by total quantity sold.
    
    Returns: list of tuples (ProductName, TotalQuantity, TotalRevenue)
    Sorted by TotalQuantity descending.
    """
    
    product_stats = {}
    
    for tx in transactions:
        try:
            product_name = tx.get("ProductName")
            quantity = int(tx.get("Quantity", 0))
            unit_price = float(tx.get("UnitPrice", 0.0))
            revenue = quantity * unit_price
        except (ValueError, TypeError):
            continue
        
        if product_name not in product_stats:
            product_stats[product_name] = {"total_quantity": 0, "total_revenue": 0.0}
            
        product_stats[product_name]["total_quantity"] += quantity
        product_stats[product_name]["total_revenue"] += revenue
        
    sorted_products = sorted(
        product_stats.items(),
        key=lambda item: item[1]["total_quantity"],
        reverse=True,
    )
    
    result =[]
    for product_name, stats in sorted_products[:n]:
        result.append((product_name, stats["total_quantity"], stats["total_revenue"]))
        
    return result


def customer_analysis(transactions):
    """
    Analyzes customer purchase patterns.
    
    Returns: dictionary sorted by total_spent descending
    {
        'C001' : {
            'total_spent': 95000.0,
            'purchase_count': 3,
            'avg_order_value': 31666.67,
            'products_bought': ['Laptop', 'Mouse']
        },
        ...
    }
    """
    
    customer_stats = {}
    
    for tx in transactions:
        try:
            customer_id = tx.get("CustomerID")
            product_name = tx.get("ProductName")
            quantity = int(tx.get("Quantity", 0))
            unit_price = float(tx.get("UnitPrice", 0.0))
            amount = quantity * unit_price
        except (ValueError, TypeError):
            continue
        
        if customer_id not in customer_stats:
            customer_stats[customer_id] = {
                "total_spent": 0.0,
                "purchase_count": 0,
                "products_bought": set(),
            }
        
        customer_stats[customer_id]["total_spent"] += amount
        customer_stats[customer_id]["purchase_count"] += 1
        
        if product_name is not None and str(product_name).strip() != "":
            customer_stats[customer_id]["products_bought"].add(product_name)
    
    for cid, stats in customer_stats.items():
        count = stats["purchase_count"]
        stats["avg_order_value"] = round(stats["total_spent"] / count, 2) if count > 0 else 0.0
        stats["products_bought"] = sorted(list(stats["products_bought"]))
        
    sorted_customer_stats = dict(
        sorted(customer_stats.items(), key=lambda item: item[1]["total_spent"], reverse=True)
    )
    return sorted_customer_stats



def  daily_sales_trend(transactions):
    """
    Analyzes sales trends by date.
    
    Returns: dictionary sorted by date (chronological)
    {
        '2024-12-01': {'revenue': ..., 'transaction_count': ..., 'unique_customers': ...},
        ...
    }
    """
    daily = {}
    
    for tx in transactions:
        try:
            date = tx.get("Date")
            customer_id = tx.get("CustomerID")
            quantity = int(tx.get("Quantity", 0))
            unit_price = float(tx.get("UnitPrice", 0.0))
            amount = quantity * unit_price
        except(ValueError, TypeError):
            continue
        
        if date not in daily:
            daily[date] = {
                "revenue": 0.0,
                "transaction_count": 0,
                "unique_customers": set(),
                }    
        
        daily[date]["revenue"] += amount
        daily[date]["transaction_count"] += 1
        
        if customer_id is not None and str(customer_id).strip() != "":
            daily[date]["unique_customers"].add(customer_id)
    
    for date in daily:
        daily[date]["unique_customers"] = len(daily[date]["unique_customers"])
        
    sorted_daily = dict(sorted(daily.items(), key=lambda item: item[0]))
    return sorted_daily


def find_peak_sales_day(transactions):
    """
    Identifies the date with highest revenue.
    
    Returns: tuple (date, revenue, transactions_count)
    Example: ('2024-12-15', 185000.0, 12)
    """
    daily_totals = {}
    
    for tx in transactions:
        try:
            date  = tx.get("Date")
            quantity = int(tx.get("Quantity", 0))
            unit_price = float(tx.get("UnitPrice", 0.0))
            amount = quantity * unit_price
        except (ValueError, TypeError):
            continue
        
        if date not in daily_totals:
            daily_totals[date] = {"revenue": 0.0, "transaction_count": 0}
            
        daily_totals[date]["revenue"] += amount
        daily_totals[date]["transaction_count"] +1
        
    if not daily_totals:
        return None, 0.0, 0
    
    peak_date, stats = max(daily_totals.items(), key=lambda item: item[1]["revenue"])
    return peak_date, stats["revenue"], stats["transaction_count"]


def low_performing_products(transactions, threshold=10):
    """
    Identifies prroducts with low sales (total quantity < threshold).
    
    Returns: list od tuples (ProductName, TotalQuantity, TotalRevenue)
    Sorted by TotalQuanitty ascending.
    """
    
    product_stats = {}
    
    for tx in transactions:
        try:
            product_name = tx.get("ProductName")
            quantity = int(tx.get("Quantity", 0))
            unit_price =float(tx.get("UnitPrice", 0.0))
            revenue = quantity * unit_price
        except(ValueError, TypeError):
            continue
        
        if product_name not in product_stats:
            product_stats[product_name]= {"total_quantity": 0, "total_revenue": 0.0}
        
        product_stats[product_name]["total_quantity"] += quantity
        product_stats[product_name]["total_revenue"] += revenue
        
    low_products = [
        (name, stats["total_quantity"], stats["total_revenue"])
        for name, stats in product_stats.items()
        if stats["total_quantity"] < threshold
    ]
    
    low_products.sort(key=lambda item: item[1])
    return low_products

    