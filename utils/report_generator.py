from __future__ import annotations

from pathlib import Path
from datetime import datetime


def _fmt_money(x):
    try:
        return f"{float(x):,.2f}"
    except Exception:
        return "0.00"


def _safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def _safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default


def _tx_amount(tx):
    qty = _safe_int(tx.get("Quantity", 0))
    price = _safe_float(tx.get("UnitPrice", 0.0))
    return qty * price


def _date_range(transactions):
    dates = [t.get("Date") for t in transactions if t.get("Date")]
    if not dates:
        return None, None
    return min(dates), max(dates)


def _region_table(transactions):
    region_stats = {}
    total = 0.0

    for t in transactions:
        region = t.get("Region", "Unknown")
        amt = _tx_amount(t)
        total += amt

        if region not in region_stats:
            region_stats[region] = {"sales": 0.0, "count": 0}

        region_stats[region]["sales"] += amt
        region_stats[region]["count"] += 1

    rows = []
    for region, s in region_stats.items():
        pct = (s["sales"] / total * 100) if total > 0 else 0.0
        rows.append((region, s["sales"], pct, s["count"]))

    rows.sort(key=lambda r: r[1], reverse=True)
    return rows, total


def _top_products(transactions, n=5):
    prod = {}

    for t in transactions:
        name = t.get("ProductName", "Unknown")
        qty = _safe_int(t.get("Quantity", 0))
        rev = _tx_amount(t)

        if name not in prod:
            prod[name] = {"qty": 0, "rev": 0.0}

        prod[name]["qty"] += qty
        prod[name]["rev"] += rev

    items = [(k, v["qty"], v["rev"]) for k, v in prod.items()]
    items.sort(key=lambda x: x[1], reverse=True)
    return items[:n]


def _top_customers(transactions, n=5):
    cust = {}

    for t in transactions:
        cid = t.get("CustomerID", "Unknown")
        amt = _tx_amount(t)

        if cid not in cust:
            cust[cid] = {"spent": 0.0, "count": 0}

        cust[cid]["spent"] += amt
        cust[cid]["count"] += 1

    items = [(k, v["spent"], v["count"]) for k, v in cust.items()]
    items.sort(key=lambda x: x[1], reverse=True)
    return items[:n]


def _daily_trend(transactions):
    daily = {}

    for t in transactions:
        date = t.get("Date", "Unknown")
        cid = t.get("CustomerID", "")
        amt = _tx_amount(t)

        if date not in daily:
            daily[date] = {"rev": 0.0, "count": 0, "customers": set()}

        daily[date]["rev"] += amt
        daily[date]["count"] += 1
        if cid:
            daily[date]["customers"].add(cid)

    rows = []
    for d, s in daily.items():
        rows.append((d, s["rev"], s["count"], len(s["customers"])))

    rows.sort(key=lambda x: x[0])
    return rows


def _peak_day(transactions):
    trend = _daily_trend(transactions)
    if not trend:
        return None, 0.0, 0
    best = max(trend, key=lambda x: x[1])
    return best[0], best[1], best[2]


def _low_performers(transactions, threshold=10):
    prod = {}

    for t in transactions:
        name = t.get("ProductName", "Unknown")
        qty = _safe_int(t.get("Quantity", 0))
        rev = _tx_amount(t)

        if name not in prod:
            prod[name] = {"qty": 0, "rev": 0.0}

        prod[name]["qty"] += qty
        prod[name]["rev"] += rev

    low = [(k, v["qty"], v["rev"]) for k, v in prod.items() if v["qty"] < threshold]
    low.sort(key=lambda x: x[1])
    return low


def _avg_tx_value_by_region(transactions):
    region = {}
    for t in transactions:
        r = t.get("Region", "Unknown")
        amt = _tx_amount(t)
        if r not in region:
            region[r] = {"total": 0.0, "count": 0}
        region[r]["total"] += amt
        region[r]["count"] += 1

    rows = []
    for r, s in region.items():
        avg = (s["total"] / s["count"]) if s["count"] > 0 else 0.0
        rows.append((r, avg))
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows


def _api_enrichment_summary(enriched_transactions):
    total = len(enriched_transactions)
    matched = sum(1 for t in enriched_transactions if t.get("API_Match") is True)
    rate = (matched / total * 100) if total > 0 else 0.0

    not_matched_ids = sorted(
        {t.get("ProductID") for t in enriched_transactions if t.get("API_Match") is False and t.get("ProductID")}
    )

    return total, matched, rate, not_matched_ids


def generate_sales_report(transactions, enriched_transactions, output_file='output/sales_report.txt'):
    """
    Generates a comprehensive formatted text report

    Report Must Include (in this order):

    1. HEADER
       - Report title
       - Generation date and time
       - Total records processed

    2. OVERALL SUMMARY
       - Total Revenue (formatted with commas)
       - Total Transactions
       - Average Order Value
       - Date Range of data

    3. REGION-WISE PERFORMANCE
       - Table showing each region with:
         * Total Sales Amount
         * Percentage of Total
         * Transaction Count
       - Sorted by sales amount descending

    4. TOP 5 PRODUCTS
       - Table with columns: Rank, Product Name, Quantity Sold, Revenue

    5. TOP 5 CUSTOMERS
       - Table with columns: Rank, Customer ID, Total Spent, Order Count

    6. DAILY SALES TREND
       - Table showing: Date, Revenue, Transactions, Unique Customers

    7. PRODUCT PERFORMANCE ANALYSIS
       - Best selling day
       - Low performing products (if any)
       - Average transaction value per region

    8. API ENRICHMENT SUMMARY
       - Total products enriched
       - Success rate percentage
       - List of products that couldn't be enriched

    Expected Output Format (sample):
    ============================================
           SALES ANALYTICS REPORT
         Generated: 2024-12-18 14:30:22
         Records Processed: 95
    ============================================

    OVERALL SUMMARY
    --------------------------------------------
    Total Revenue:        ₹15,45,000.00
    Total Transactions:   95
    Average Order Value:  ₹16,263.16
    Date Range:           2024-12-01 to 2024-12-31

    REGION-WISE PERFORMANCE
    --------------------------------------------
    Region    Sales         % of Total  Transactions
    North     ₹4,50,000     29.13%      25
    South     ₹3,80,000     24.60%      22
    ...

    (continue with all sections...)
    """

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records_processed = len(transactions)

    total_revenue = sum(_tx_amount(t) for t in transactions)
    total_tx = len(transactions)
    avg_order_value = (total_revenue / total_tx) if total_tx > 0 else 0.0
    start_date, end_date = _date_range(transactions)

    region_rows, grand_total = _region_table(transactions)
    top_products = _top_products(transactions, n=5)
    top_customers = _top_customers(transactions, n=5)
    daily_rows = _daily_trend(transactions)

    peak_date, peak_rev, peak_count = _peak_day(transactions)
    low_products = _low_performers(transactions, threshold=10)
    avg_region_rows = _avg_tx_value_by_region(transactions)

    api_total, api_matched, api_rate, api_unmatched = _api_enrichment_summary(enriched_transactions)

    lines = []

    # 1) HEADER
    lines.append("=" * 45)
    lines.append("SALES ANALYTICS REPORT")
    lines.append(f"Generated: {now}")
    lines.append(f"Records Processed: {records_processed}")
    lines.append("=" * 45)
    lines.append("")

    # 2) OVERALL SUMMARY
    lines.append("OVERALL SUMMARY")
    lines.append("-" * 45)
    lines.append(f"Total Revenue:      {_fmt_money(total_revenue)}")
    lines.append(f"Total Transactions: {total_tx}")
    lines.append(f"Average Order Value:{_fmt_money(avg_order_value)}")
    if start_date and end_date:
        lines.append(f"Date Range:         {start_date} to {end_date}")
    else:
        lines.append("Date Range:         N/A")
    lines.append("")

    # 3) REGION-WISE PERFORMANCE
    lines.append("REGION-WISE PERFORMANCE")
    lines.append("-" * 45)
    lines.append(f"{'Region':<12}{'Sales':>15}{'% of Total':>12}{'Transactions':>14}")
    for r, sales, pct, cnt in region_rows:
        lines.append(f"{str(r):<12}{_fmt_money(sales):>15}{pct:>12.2f}{cnt:>14}")
    lines.append("")

    # 4) TOP 5 PRODUCTS
    lines.append("TOP 5 PRODUCTS")
    lines.append("-" * 45)
    lines.append(f"{'Rank':<6}{'Product Name':<22}{'Qty Sold':>10}{'Revenue':>12}")
    for i, (name, qty, rev) in enumerate(top_products, start=1):
        lines.append(f"{i:<6}{str(name)[:21]:<22}{qty:>10}{_fmt_money(rev):>12}")
    lines.append("")

    # 5) TOP 5 CUSTOMERS
    lines.append("TOP 5 CUSTOMERS")
    lines.append("-" * 45)
    lines.append(f"{'Rank':<6}{'Customer ID':<14}{'Total Spent':>14}{'Orders':>10}")
    for i, (cid, spent, cnt) in enumerate(top_customers, start=1):
        lines.append(f"{i:<6}{str(cid):<14}{_fmt_money(spent):>14}{cnt:>10}")
    lines.append("")

    # 6) DAILY SALES TREND
    lines.append("DAILY SALES TREND")
    lines.append("-" * 45)
    lines.append(f"{'Date':<12}{'Revenue':>14}{'Transactions':>14}{'Unique Customers':>18}")
    for d, rev, cnt, uniq in daily_rows:
        lines.append(f"{str(d):<12}{_fmt_money(rev):>14}{cnt:>14}{uniq:>18}")
    lines.append("")

    # 7) PRODUCT PERFORMANCE ANALYSIS
    lines.append("PRODUCT PERFORMANCE ANALYSIS")
    lines.append("-" * 45)
    lines.append(f"Best Selling Day: {peak_date if peak_date else 'N/A'} "
                 f"(Revenue {_fmt_money(peak_rev)}, Transactions {peak_count})")
    lines.append("")

    lines.append("Low Performing Products (Quantity < 10)")
    if low_products:
        lines.append(f"{'Product Name':<22}{'Qty':>6}{'Revenue':>12}")
        for name, qty, rev in low_products:
            lines.append(f"{str(name)[:21]:<22}{qty:>6}{_fmt_money(rev):>12}")
    else:
        lines.append("None")
    lines.append("")

    lines.append("Average Transaction Value by Region")
    lines.append(f"{'Region':<12}{'Avg Transaction Value':>22}")
    for r, avg in avg_region_rows:
        lines.append(f"{str(r):<12}{_fmt_money(avg):>22}")
    lines.append("")

    # 8) API ENRICHMENT SUMMARY
    lines.append("API ENRICHMENT SUMMARY")
    lines.append("-" * 45)
    lines.append(f"Total Transactions Enriched: {api_total}")
    lines.append(f"Successfully Enriched:       {api_matched}")
    lines.append(f"Success Rate:               {api_rate:.2f}%")
    lines.append("")
    lines.append("Products that couldn't be enriched (ProductID):")
    if api_unmatched:
        lines.append(", ".join(api_unmatched))
    else:
        lines.append("None")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path)
