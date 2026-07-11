"""
download_city_data.py — Downloader script for multi-city Inside Airbnb datasets.

Fetches real listings, calendar, reviews, and neighborhood files for Boston
and San Francisco from Inside Airbnb servers, decompresses them, and saves
them in the data/raw/ directory.
"""

import os
import argparse
import gzip
import shutil
import requests

# Exact URLs scraped from Inside Airbnb index page
CITY_URLS = {
    "boston": {
        "listings": "https://data.insideairbnb.com/united-states/ma/boston/2026-06-15/data/listings.csv.gz",
        "calendar": "https://data.insideairbnb.com/united-states/ma/boston/2026-06-15/data/calendar.csv.gz",
        "reviews": "https://data.insideairbnb.com/united-states/ma/boston/2026-06-15/data/reviews.csv.gz",
        "neighbourhoods": "https://data.insideairbnb.com/united-states/ma/boston/2026-06-15/visualisations/neighbourhoods.csv"
    },
    "sf": {
        "listings": "https://data.insideairbnb.com/united-states/ca/san-francisco/2026-06-14/data/listings.csv.gz",
        "calendar": "https://data.insideairbnb.com/united-states/ca/san-francisco/2026-06-14/data/calendar.csv.gz",
        "reviews": "https://data.insideairbnb.com/united-states/ca/san-francisco/2026-06-14/data/reviews.csv.gz",
        "neighbourhoods": "https://data.insideairbnb.com/united-states/ca/san-francisco/2026-06-14/visualisations/neighbourhoods.csv"
    }
}


def download_and_extract_city(city):
    """Download and extract listings, calendar, reviews, and neighbourhoods for a city."""
    if city not in CITY_URLS:
        print(f"Error: Unknown city '{city}'")
        return False

    print(f"\n==================================================")
    print(f"Active Market Ingestion: {city.upper()}")
    print(f"==================================================")

    raw_dir = f"data/raw/{city}"
    os.makedirs(raw_dir, exist_ok=True)

    urls = CITY_URLS[city]
    for name, url in urls.items():
        print(f"\n[Ingest] Downloading {name} from:")
        print(f"   {url}")

        # Local file paths
        is_gz = url.endswith(".gz")
        local_filename = f"{name}.csv.gz" if is_gz else f"{name}.csv"
        local_path = os.path.join(raw_dir, local_filename)
        final_csv_path = os.path.join(raw_dir, f"{name}.csv")

        # Download stream
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"[OK] Saved file: {local_path}")
        except Exception as e:
            print(f"[ERROR] Failed to download {name}: {e}")
            return False

        # Decompress if needed
        if is_gz:
            try:
                print(f"[Decompress] Extracting Gzip file to {final_csv_path}...")
                with gzip.open(local_path, "rb") as f_in:
                    with open(final_csv_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                print(f"[OK] Extracted successfully.")
                # Clean up the compressed gzip file to save space
                os.remove(local_path)
            except Exception as e:
                print(f"[ERROR] Failed to decompress {name}: {e}")
                return False

    print(f"[SUCCESS] Ingested all raw CSVs for {city.upper()}!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Ingest multi-city datasets from Inside Airbnb.")
    parser.add_argument(
        "--city",
        type=str,
        default="all",
        choices=["all", "boston", "sf"],
        help="City to download (default: all)"
    )
    args = parser.parse_args()

    cities = ["boston", "sf"] if args.city == "all" else [args.city]
    success = True

    for city in cities:
        if not download_and_extract_city(city):
            success = False

    if success:
        print("\nAll requested datasets retrieved successfully!")
    else:
        print("\nIngestion completed with some errors.")


if __name__ == "__main__":
    main()
