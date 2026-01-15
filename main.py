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

def main():
    raw = read_sales_data("data/sales_data.txt")
    parsed = parse_transactions(raw)
    valid, invalid_count, summary = validate_and_filter(parsed)

    print("PART 3 TEST")
    print("Valid:", len(valid), "| Invalid:", invalid_count)

    products = fetch_all_products()
    mapping = create_product_mapping(products)
    
    enriched = enrich_sales_data(valid, mapping)
    
    matched = sum(1 for t in enriched if t.get("API_Match") is True)
    print(f"Enriched matches: {matched}/{len(enriched)}")
    print("Saved file: data/enriched_sales_data.txt")

if __name__ == "__main__":
    main()

