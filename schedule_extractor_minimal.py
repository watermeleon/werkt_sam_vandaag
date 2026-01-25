"""
Minimal Schedule Extractor using Cell Coordinates
"""

import pdfplumber
import pandas as pd
import calendar
from cell_detector import CellDetector
import warnings
warnings.filterwarnings("ignore")


import os
import sys

# Suppress all stderr output
sys.stderr = open(os.devnull, 'w')

class ScheduleExtractor:
    """Extract schedule data using cell coordinates."""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.detector = CellDetector(pdf_path)
        
    def extract_schedule(self, year: int, month: int, only_sam=True) -> pd.DataFrame:
        """
        Extract schedule for given year and month.
        
        Args:
            year: Year (e.g., 2026)
            month: Month (1-12)
            
        Returns:
            DataFrame with columns: Employee, Role, Date, Day, Shift
        """
        # Detect cells
        self.detector.detect_cells()
        cells = self.detector.cells
        
        # Days in month
        days_in_month = calendar.monthrange(year, month)[1]
        
        # Identify structure
        # Row 0: header info
        # Row 1: dates header
        # Row 2+: employee data
        # Column 0: employee name
        # Column 1: role
        # Column 2+: day shifts
        
        records = []
        
        # Process employee rows (starting from row 2)
        employee_rows = sorted(set(c['row'] for c in cells if c['row'] >= 2))
        
        print(f"Processing {len(employee_rows)} employee rows...")
        
        for row_idx in employee_rows:
            # Get employee name (column 0)
            employee = self._get_cell_text(row_idx, 0)
            
            if not employee:
                continue
            
            if only_sam:
                if not employee.strip().lower().startswith("sam"):
                    continue

                
            if employee.lower().startswith(('versie', 'speciale', 'ilja', 'tamara', 'florine', 'daphne')):
                continue
            
            print(f"  Row {row_idx}: {employee}")
            
            # Get role (column 1)
            role = self._get_cell_text(row_idx, 1)
            
            # Get shifts for each day (columns 2+)
            for day in range(1, days_in_month + 1):
                col_idx = day + 2  # +1 because column 0=name, 1=role, 2=day1, 3=day2, etc.
                
                shift = self._get_cell_text(row_idx, col_idx)
                
                date = f"{year}-{month:02d}-{day:02d}"
                
                records.append({
                    'Employee': employee,
                    'Role': role,
                    'Date': date,
                    'Day': day,
                    'Shift': shift
                })
        
        print(f"Created {len(records)} records")
        return pd.DataFrame(records)
    
    def _get_cell_text(self, row: int, col: int) -> str:
        """Extract text from a specific cell."""
        # Find the cell
        cell = next((c for c in self.detector.cells if c['row'] == row and c['col'] == col), None)
        
        if not cell:
            return ""
        
        # Extract text within cell bounds (no margins)
        with pdfplumber.open(self.pdf_path) as pdf:
            page = pdf.pages[0]
            
            # Use exact cell boundaries
            bbox = (cell['x0'], cell['y0'], cell['x1'], cell['y1'])
            
            cropped = page.within_bbox(bbox)
            text = cropped.extract_text()
            
            # Clean text
            if text:
                text = text.strip().replace('\n', ' ')
            
            return text if text else ""


def main():
    """Extract and save schedule."""
    
    # pdf_path = "./uploads/Januari_Rooster_Den_Helder_2026.pdf"
    pdf_path = "./pdfs/Januari Rooster Den Helder 2026.pdf"
    # pdf_path = "./pdfs/jan_denhelder_repaired2.pdf"

    
    print("Extracting schedule...")
    extractor = ScheduleExtractor(pdf_path)
    schedule = extractor.extract_schedule(year=2026, month=1, only_sam=True)
    
    if schedule.empty:
        print("ERROR: No records extracted!")
        return
    
    print(f"Extracted {len(schedule)} records for {schedule['Employee'].nunique()} employees")
    
    # Save to files
    schedule.to_csv("./outputs/schedule_extracted5.csv", index=False)
    schedule.to_excel("./outputs/schedule_extracted5.xlsx", index=False)
    
    # Show sample
    print("\nSample data (Sam, first 10 days):")
    sam = schedule[schedule['Employee'].str.contains('Sam', case=False, na=False)]
    print(sam.head(10)[['Employee', 'Date', 'Day', 'Shift']].to_string(index=False))
    
    print("\nFiles saved:")
    print("  - schedule_extracted.csv")
    print("  - schedule_extracted.xlsx")


if __name__ == "__main__":
    main()