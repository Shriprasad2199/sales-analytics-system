from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional

import requests


BASE_URL = "https://dummyjson.com/products"


def fetch_all_products() -> List[Dict[str, Any]]:
    """
    Fetches all products from DummyJSON API.
    
    Returns: list of product dictionaries 
    [
        {'id': 1, 'title': 'iPhone 9', 'category': 'smartphones', 'brand': 'Apple',
        'price': 549, 'rating': 4.69},
        ...
    ]
    
    Requirements:
    - Fetch all available products (use limit =100)
    - Handle connection errors with try-except
    - Return empty list if API fails
    - Print status message (success/failure)
    """
    
    url = f"{BASE_URL}?limit=100"
    
    try:
        resp = requests.get(url, timeout=100)
        resp.raise_for_status()
        playload = resp.json()
        
        products = playload.get("products", [])
        results = []
        
        for p in products:
            results.append(
                {
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "category": p.get("category"),
                    "brand": p.get("brand"),
                    "price": p.get("Price"),
                    "rating": p.get("rating"),
                }
            )
        
        print(f"API Success: Fetched {len(results)} products.")
        return results
    
    except Exception as e:
        print(f"API Failure: Could not fetch products. Error: {e}")
        return[]
    

def create_product_mapping(api_products: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Creates a mapping of product IDs to product info
    
    Parameters: api_products from fetch_all_products()
    
    Expected output:
    {
        1: {'title': 'iPhone 9', ''category': 'smartphones', 'brand': 'Apple', 'rating': 4.69},
        2: {'title': 'iPhone X', ''category': 'smartphones', 'brand': 'Apple', 'rating': 4.44},
        ...
    }
    """
    
    product_map: Dict[int, Dict[str, Any]] = {}
    
    for product in api_products:
        if not isinstance(product, dict):
            continue
        
        pid = product.get("id")
        if pid is None:
            continue
        
        try:
            pid_int = int(pid)
        except (ValueError, TypeError):
            continue
        
        product_map[pid_int] = {
            "title": product.get("title"),
            "category": product.get("category"),
            "brand": product.get("brand"),
            "rating": product.get("rating"),
        }
        
    return product_map


def _extract_numeric_product_id(product_id: Optional[str]) -> Optional[int]:
    """
    Extract numeric ID from ProductID strings like:
    'P101' -> 101, 'P5' -> 5
    
    if ID is above 100 (DummyJSON max), map into 1-100 range

    Returns: int or None
    """
    
    if product_id is None:
        return None
    
    s = str(product_id).strip()
    if s == "":
        return None
    
    if s[:1].upper() == "P":
        s = s[1:].strip()
        
    try:
        numeric_id = int(s)
    except ValueError:
        return None
    
    if numeric_id <= 0:
        return None
    
    numeric_id = ((numeric_id -1) % 100) + 1
    return numeric_id


def enrich_sales_data(transactions, product_mapping):
    """
    Enriches transaction data with API product information

    Parameters:
    - transactions: list of transaction dictionaries
    - product_mapping: dictionary from create_product_mapping()

    Returns: list of enriched transaction dictionaries

    Expected Output Format (each transaction):
    {
        'TransactionID': 'T001',
        'Date': '2024-12-01',
        'ProductID': 'P101',
        'ProductName': 'Laptop',
        'Quantity': 2,
        'UnitPrice': 45000.0,
        'CustomerID': 'C001',
        'Region': 'North',
        # NEW FIELDS ADDED FROM API:
        'API_Category': 'laptops',
        'API_Brand': 'Apple',
        'API_Rating': 4.7,
        'API_Match': True  # True if enrichment successful, False otherwise
    }

    Enrichment Logic:
    - Extract numeric ID from ProductID (P101 → 101, P5 → 5)
    - If ID exists in product_mapping, add API fields
    - If ID doesn't exist, set API_Match to False and other fields to None
    - Handle all errors gracefully

    File Output:
    - Save enriched data to 'data/enriched_sales_data.txt'
    - Use same pipe-delimited format
    - Include new columns in header
    """
    
    enriched = []
    
    for tx in transactions:
        tx_new = dict(tx) if isinstance(tx, dict) else {}
        
        try:
            numeric_id = _extract_numeric_product_id(tx_new.get("ProductID"))

            if numeric_id is not None and int(numeric_id) in product_mapping:
                info = product_mapping[int(numeric_id)]
                tx_new["API_Category"] = info.get("category")
                tx_new["API_Brand"] = info.get("brand")
                tx_new["API_Rating"] = info.get("rating")
                tx_new["API_Match"] = True
            else:
                tx_new["API_Category"] = None
                tx_new["API_Brand"] = None
                tx_new["API_Rating"] = None
                tx_new["API_Match"] = False
                
        
        except Exception:
            tx_new["API_Category"] = None
            tx_new["API_Brand"] = None
            tx_new["API_Rating"] = None
            tx_new["API_Match"] = False
        
        enriched.append(tx_new)
    
    save_enriched_data(enriched, filename= "data/enriched_sales_data.txt")
    return enriched



def save_enriched_data(enriched_transactions: List[Dict[str, Any]], filename='data/enriched_sales_data.txt'):
    """
    Saves enriched transactions back to file

    Expected File Format:
    TransactionID|Date|ProductID|ProductName|Quantity|UnitPrice|CustomerID|Region|API_Category|API_Brand|API_Rating|API_Match
    T001|2024-12-01|P101|Laptop|2|45000.0|C001|North|laptops|Apple|4.7|True
    ...

    Requirements:
    - Create output file with all original + new fields
    - Use pipe delimiter
    - Handle None values appropriately
    """
    
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    headers = [
        "TransactonID",
        "Date",
        "ProductID",
        "ProductName",
        "Quantity",
        "UnitPrice",
        "CustomerID",
        "Region",
        "API_Category",
        "API_Brand",
        "API_Rating",
        "API_Match",
    ]
    
    
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("|".join(headers) + "\n")
        
        for tx in enriched_transactions:
            row = []
            for h in headers:
                val = tx.get(h) if isinstance(tx, dict) else None
                row.append("" if val is None else str(val))
            f.write("|".join(row) + "\n")
