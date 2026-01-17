from utils.file_handler import read_sales_data
from utils.data_processor import (
    parse_transactions,
    validate_and_filter,
    calculate_total_revenue,
    region_wise_sales,
    top_selling_products,
    customer_analysis,
    daily_sales_trend,
    find_peak_sales_day,
    low_performing_products,
)
from utils.api_handler import fetch_all_products, create_product_mapping, enrich_sales_data
from utils.report_generator import generate_sales_report


def _print_header():
    print("=" * 50)
    print("SALES ANALYTICS SYSTEM")
    print("=" * 50)


def _get_filter_input(available_regions, min_amt, max_amt):
    """
    Ask user if they want filtering and collect filter parameters safely.
    Returns: (region, min_amount, max_amount)
    """
    print("\n[3/10] Filter Options Available:")
    if available_regions:
        print("Regions:", ", ".join(available_regions))
    else:
        print("Regions: (none found)")

    print(f"Amount Range: {min_amt:.0f} - {max_amt:.0f}")

    choice = input("\nDo you want to filter data? (y/n): ").strip().lower()
    if choice != "y":
        return None, None, None

    region = input("Enter region (or press Enter to skip): ").strip()
    if region == "":
        region = None

    min_amount = input("Enter minimum amount (or press Enter to skip): ").strip()
    max_amount = input("Enter maximum amount (or press Enter to skip): ").strip()

    def to_float_or_none(x):
        if x is None:
            return None
        x = x.strip()
        if x == "":
            return None
        try:
            return float(x)
        except ValueError:
            return None

    return region, to_float_or_none(min_amount), to_float_or_none(max_amount)


def main():
    _print_header()

    try:
        # 1) Read sales data
        print("\n[1/10] Reading sales data...")
        raw_lines = read_sales_data("data/sales_data.txt")
        print(f"✓ Successfully read {len(raw_lines)} transactions")

        # 2) Parse and clean
        print("\n[2/10] Parsing and cleaning data...")
        parsed = parse_transactions(raw_lines)
        print(f"✓ Parsed {len(parsed)} records")

        # 3) Show filter options (regions + amount range) BEFORE filtering
        # We compute these from parsed records (even if some will be invalid later)
        regions = sorted({t.get("Region") for t in parsed if t.get("Region")})
        amounts = []
        for t in parsed:
            try:
                amt = int(t.get("Quantity", 0)) * float(t.get("UnitPrice", 0.0))
                amounts.append(amt)
            except Exception:
                continue
        min_amt = min(amounts) if amounts else 0.0
        max_amt = max(amounts) if amounts else 0.0

        region_filter, min_amount, max_amount = _get_filter_input(regions, min_amt, max_amt)

        # 4) Validate and filter
        print("\n[4/10] Validating transactions...")
        valid, invalid_count, summary = validate_and_filter(
            parsed,
            region=region_filter,
            min_amount=min_amount,
            max_amount=max_amount,
        )
        print(f"✓ Valid: {len(valid)} | Invalid: {invalid_count}")

        # 5) Analytics (Part 2)
        print("\n[5/10] Analyzing sales data...")
        _ = calculate_total_revenue(valid)
        _ = region_wise_sales(valid)
        _ = top_selling_products(valid, n=5)
        _ = customer_analysis(valid)
        _ = daily_sales_trend(valid)
        _ = find_peak_sales_day(valid)
        _ = low_performing_products(valid, threshold=10)
        print("✓ Analysis complete")

        # 6) Fetch API products
        print("\n[6/10] Fetching product data from API...")
        api_products = fetch_all_products()
        product_mapping = create_product_mapping(api_products)

        # 7) Enrich sales data + save enriched file (Part 3)
        print("\n[7/10] Enriching sales data...")
        enriched = enrich_sales_data(valid, product_mapping)

        enriched_count = sum(1 for t in enriched if t.get("API_Match") is True)
        rate = (enriched_count / len(enriched) * 100) if enriched else 0.0
        print(f"✓ Enriched {enriched_count}/{len(enriched)} transactions ({rate:.1f}%)")

        # 8) Save enriched file already handled inside enrich_sales_data()
        print("\n[8/10] Saving enriched data...")
        print("✓ Saved to: data/enriched_sales_data.txt")

        # 9) Generate report (Part 4)
        print("\n[9/10] Generating report...")
        report_path = generate_sales_report(valid, enriched, output_file="output/sales_report.txt")
        print(f"✓ Report saved to: {report_path}")

        # 10) Done
        print("\n[10/10] Process Complete!")
        print("=" * 50)

    except FileNotFoundError as e:
        print(f"\nError: {e}")
    except Exception as e:
        print(f"\nUnexpected error occurred: {e}")


if __name__ == "__main__":
    main()
