from schedule_extractor_minimal import ScheduleExtractor
import time
import os
from pathlib import Path
import pandas as pd
import re


# Location names (case-insensitive matching)
LOCATIONS = ["Den Helder", "Alkmaar"]

# Dutch month names to month numbers
DUTCH_MONTHS = {
    "januari": 1,
    "februari": 2,
    "maart": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "augustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}


def parse_pdf_filename(pdf_path: str) -> dict | None:
    """
    Auto-detect location, month, and year from PDF filename.
    Expected format: "Februari Rooster Den Helder 2026.pdf"

    Returns dict with 'location', 'month', 'year' or None if parsing fails.
    """
    filename = Path(pdf_path).stem  # Get filename without extension
    filename_lower = filename.lower()

    # Detect location
    location = None
    for loc in LOCATIONS:
        if loc.lower() in filename_lower:
            location = loc
            break

    # Detect month
    month = None
    for month_name, month_num in DUTCH_MONTHS.items():
        if month_name in filename_lower:
            month = month_num
            break

    # Detect year (look for 4-digit number starting with 20)
    year = None
    year_match = re.search(r'20\d{2}', filename)
    if year_match:
        year = int(year_match.group())

    if location is None or month is None or year is None:
        print(f"  WARNING: Could not parse filename '{filename}'")
        print(f"    Location: {location}, Month: {month}, Year: {year}")
        return None

    return {"location": location, "month": month, "year": year}


def get_dest_filename(pdf_path: str, parsed_info: dict) -> str:
    """Generate destination filename based on parsed info."""
    month_name = list(DUTCH_MONTHS.keys())[parsed_info["month"] - 1].capitalize()
    location_clean = parsed_info["location"].replace(" ", "_")
    return f"sam_schedule_{parsed_info['year']}_{parsed_info['month']:02d}_{month_name}_{location_clean}.csv"


def get_sams_schedule(pdf_path: str, year: int, month: int) -> pd.DataFrame:
    """Extract Sam's schedule from a PDF file."""
    print(f"  Extracting schedule...")
    start_time = time.time()
    extractor = ScheduleExtractor(pdf_path)
    schedule = extractor.extract_schedule(year=year, month=month, only_sam=True)
    print(f"  Time taken: {time.time() - start_time:.2f} seconds")

    if schedule.empty:
        print("  No records for Sam in this schedule")
        return pd.DataFrame()  # Return empty DataFrame

    sam = schedule[schedule['Employee'].str.contains('Sam', case=False, na=False)]
    print(f"  Extracted {len(sam)} records for Sam")
    return sam


def process_all_pdfs(source_path: str, dest_path: str, skip_if_exist: bool = True):
    """
    Process all PDFs in source folder and extract Sam's schedules.

    Args:
        source_path: Path to folder containing PDF files
        dest_path: Path to folder where extracted schedules will be saved
        skip_if_exist: If True, skip PDFs that already have a destination file
    """
    # Ensure destination folder exists
    Path(dest_path).mkdir(parents=True, exist_ok=True)

    # Get all PDF files
    pdf_files = list(Path(source_path).glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {source_path}\n")

    results = {"processed": [], "skipped": [], "failed": []}

    for pdf_path in sorted(pdf_files):
        print(f"Processing: {pdf_path.name}")

        # Parse filename to get location, month, year
        parsed = parse_pdf_filename(str(pdf_path))
        if parsed is None:
            print(f"  FAILED: Could not parse filename\n")
            results["failed"].append(str(pdf_path))
            continue

        print(f"  Detected: {parsed['location']}, {list(DUTCH_MONTHS.keys())[parsed['month']-1].capitalize()} {parsed['year']}")

        # Generate destination filename
        dest_filename = get_dest_filename(str(pdf_path), parsed)
        dest_file = Path(dest_path) / dest_filename

        # Check if destination already exists
        if skip_if_exist and dest_file.exists():
            print(f"  SKIPPED: Destination file already exists\n")
            results["skipped"].append(str(pdf_path))
            continue

        # Extract schedule
        try:
            sam_schedule = get_sams_schedule(str(pdf_path), parsed["year"], parsed["month"])

            # Save to CSV (even if empty, to mark as processed)
            sam_schedule.to_csv(dest_file, index=False)
            print(f"  SAVED: {dest_filename}\n")
            results["processed"].append(str(pdf_path))

        except Exception as e:
            print(f"  FAILED: {e}\n")
            results["failed"].append(str(pdf_path))

    # Summary
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Processed: {len(results['processed'])}")
    print(f"Skipped:   {len(results['skipped'])}")
    print(f"Failed:    {len(results['failed'])}")

    return results



def main():
        

    source_path = "./pdfs/"
    dest_path = "./extracted_schedules/"

    print("hi")
    # Run the batch processing
    results = process_all_pdfs(source_path, dest_path, skip_if_exist=True)

if __name__ == "__main__":
    main()