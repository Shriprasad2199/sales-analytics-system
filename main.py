from utils.file_handler import read_sales_data
from utils.data_processor import parse_transactions, validate_and_filter


def main():
    raw = read_sales_data("data/sales_data.txt")
    parsed = parse_transactions(raw)
    valid, invalid_count, summary = validate_and_filter(parsed)

    print("PART 1 TEST RESULTS")
    print("Raw lines:", len(raw))
    print("Parsed transactions:", len(parsed))
    print("Valid transactions:", len(valid))
    print("Invalid removed:", invalid_count)
    print("Summary:", summary)


if __name__ == "__main__":
    main()
