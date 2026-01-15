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


def main():
    raw = read_sales_data("data/sales_data.txt")
    parsed = parse_transactions(raw)
    valid, invalid_count, summary = validate_and_filter(parsed)

    print("PART 2 TEST RESULTS")
    print("Valid transactions:", len(valid), "| Invalid removed:", invalid_count)

    total_rev = calculate_total_revenue(valid)
    print("Total revenue:", total_rev)

    print("\nRegion-wise sales (top 2):")
    reg = region_wise_sales(valid)
    for k in list(reg.keys())[:2]:
        print(k, reg[k])

    print("\nTop 5 products:")
    print(top_selling_products(valid, n=5))

    print("\nTop 3 customers:")
    cust = customer_analysis(valid)
    for k in list(cust.keys())[:3]:
        print(k, cust[k])

    print("\nDaily sales trend (first 3 days):")
    trend = daily_sales_trend(valid)
    for d in list(trend.keys())[:3]:
        print(d, trend[d])

    print("\nPeak sales day:")
    print(find_peak_sales_day(valid))

    print("\nLow performing products (<10):")
    print(low_performing_products(valid, threshold=10))


if __name__ == "__main__":
    main()

