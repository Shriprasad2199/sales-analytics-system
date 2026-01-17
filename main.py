from utils.file_handler import read_sales_data
from utils.data_processor import parse_transactions, validate_and_filter
from utils.api_handler import fetch_all_products, create_product_mapping, enrich_sales_data
from utils.report_generator import generate_sales_report


def main():
    raw = read_sales_data("data/sales_data.txt")
    parsed = parse_transactions(raw)
    valid, invalid_count, summary = validate_and_filter(parsed)

    products = fetch_all_products()
    mapping = create_product_mapping(products)
    enriched = enrich_sales_data(valid, mapping)

    report_path = generate_sales_report(valid, enriched, output_file="output/sales_report.txt")
    print("Report saved to:", report_path)
    
    
    
if __name__ == "__main__":
    main()
