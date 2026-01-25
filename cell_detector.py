"""
Cell Coordinate Detector with Visualization
============================================

Detects the exact boundaries of each cell in the PDF table
and creates a visual overlay to verify detection accuracy.
"""

import pdfplumber
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from pathlib import Path

import warnings
warnings.filterwarnings("ignore")

class CellDetector:
    """Detect and visualize table cell boundaries in PDF."""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.cells = []
        self.page = None
        self.surpress_warnings = True
        
    def detect_cells(self):
        """
        Detect all cell boundaries in the PDF table.
        
        Returns:
            List of cell dictionaries with coordinates
        """
        print("Opening PDF and detecting cell boundaries...")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            self.page = pdf.pages[0]
            
            # Get page dimensions
            page_width = self.page.width
            page_height = self.page.height
            print(f"  Page size: {page_width} x {page_height}")
            
            # Method 1: Try to use pdfplumber's table detection
            print("\n[Method 1] Using pdfplumber table detection...")
            tables = self.page.find_tables()
            
            if tables:
                table = tables[0]
                print(f"  Found table with {len(table.rows)} rows and {len(table.rows[0].cells) if table.rows else 0} columns")
                
                # Extract cell coordinates
                self.cells = []
                for row_idx, row in enumerate(table.rows):
                    for col_idx, cell in enumerate(row.cells):
                        if cell:
                            self.cells.append({
                                'row': row_idx,
                                'col': col_idx,
                                'x0': cell[0],  # left
                                'y0': cell[1],  # top
                                'x1': cell[2],  # right
                                'y1': cell[3],  # bottom
                                'width': cell[2] - cell[0],
                                'height': cell[3] - cell[1]
                            })
                
                print(f"  Detected {len(self.cells)} cells (before fixing)")
                
                # Fix the cells using name column as reference
                print("\n[Method 2] Fixing cell boundaries using name column as reference...")
                self._fix_cells_using_name_column()
                
            else:
                print("  No tables found with Method 1")
                
                # Method 2: Detect cells from lines
                print("\n[Method 2] Detecting cells from lines...")
                self._detect_cells_from_lines()
            
            return self.cells
    
    def _fix_cells_using_name_column(self):
        """
        Fix cell boundaries by using:
        - Horizontal lines from name column (column 0) - one row per employee
        - Vertical lines from ORIGINAL detection - proper schedule alignment
        """
        
        # Step 1: Extract horizontal boundaries from column 0 (name column)
        print("  Step 1: Extracting horizontal boundaries from name column...")
        
        name_col_cells = [c for c in self.cells if c['col'] == 0]
        name_col_cells.sort(key=lambda c: c['row'])
        
        # Get unique Y-coordinates (top and bottom of each cell)
        horizontal_lines = set()
        for cell in name_col_cells:
            horizontal_lines.add(cell['y0'])
            horizontal_lines.add(cell['y1'])
        
        horizontal_lines = sorted(list(horizontal_lines))
        print(f"     Found {len(horizontal_lines)} horizontal boundaries")
        
        # Step 2: Extract vertical boundaries from ORIGINAL table detection
        # Get all unique X-coordinates from original cells
        print("  Step 2: Extracting vertical boundaries from original detection...")
        
        # Get vertical lines from cells in a data row (not header, not name column)
        # Use row 2 (first employee row) to get the proper column structure
        row2_cells = [c for c in self.cells if c['row'] == 2 and c['col'] > 1]
        row2_cells.sort(key=lambda c: c['col'])
        
        vertical_lines = set()
        # Always include the leftmost boundary
        vertical_lines.add(min(c['x0'] for c in self.cells))
        
        # Add boundaries from row 2 (which has the proper schedule column structure)
        for cell in row2_cells:
            vertical_lines.add(cell['x0'])
            vertical_lines.add(cell['x1'])
        
        # Also add the name and role column boundaries from column 0 and 1
        for cell in self.cells:
            if cell['col'] in [0, 1]:
                vertical_lines.add(cell['x0'])
                vertical_lines.add(cell['x1'])
        
        vertical_lines = sorted(list(vertical_lines))
        print(f"     Found {len(vertical_lines)} vertical boundaries")
        
        # Step 3: Reconstruct ALL cells
        print("  Step 3: Reconstructing all cells...")
        
        new_cells = []
        
        for row_idx in range(len(horizontal_lines) - 1):
            for col_idx in range(len(vertical_lines) - 1):
                x0 = vertical_lines[col_idx]
                x1 = vertical_lines[col_idx + 1]
                y0 = horizontal_lines[row_idx]
                y1 = horizontal_lines[row_idx + 1]
                
                width = x1 - x0
                height = y1 - y0
                
                # Skip very small cells
                if width < 5 or height < 5:
                    continue
                
                new_cells.append({
                    'row': row_idx,
                    'col': col_idx,
                    'x0': x0,
                    'y0': y0,
                    'x1': x1,
                    'y1': y1,
                    'width': width,
                    'height': height
                })
        
        self.cells = new_cells
        print(f"     Created {len(self.cells)} cells")
        
        # Verify structure
        unique_rows = len(set(c['row'] for c in self.cells))
        unique_cols = len(set(c['col'] for c in self.cells))
        print(f"     Grid: {unique_rows} rows × {unique_cols} columns")
    
    def _detect_cells_from_lines(self):
        """Detect cells by finding intersections of horizontal and vertical lines."""
        
        # Get all lines on the page
        horizontal_lines = []
        vertical_lines = []
        
        # Extract lines (this gets line objects from PDF)
        if hasattr(self.page, 'lines'):
            for line in self.page.lines:
                x0, y0, x1, y1 = line['x0'], line['top'], line['x1'], line['bottom']
                
                # Horizontal line (y0 ≈ y1)
                if abs(y0 - y1) < 2:
                    horizontal_lines.append({'y': y0, 'x0': min(x0, x1), 'x1': max(x0, x1)})
                
                # Vertical line (x0 ≈ x1)
                elif abs(x0 - x1) < 2:
                    vertical_lines.append({'x': x0, 'y0': min(y0, y1), 'y1': max(y0, y1)})
        
        print(f"  Found {len(horizontal_lines)} horizontal lines")
        print(f"  Found {len(vertical_lines)} vertical lines")
        
        if horizontal_lines and vertical_lines:
            # Sort lines
            horizontal_lines.sort(key=lambda l: l['y'])
            vertical_lines.sort(key=lambda l: l['x'])
            
            # Create cells from line intersections
            self.cells = []
            for row_idx in range(len(horizontal_lines) - 1):
                for col_idx in range(len(vertical_lines) - 1):
                    x0 = vertical_lines[col_idx]['x']
                    x1 = vertical_lines[col_idx + 1]['x']
                    y0 = horizontal_lines[row_idx]['y']
                    y1 = horizontal_lines[row_idx + 1]['y']
                    
                    self.cells.append({
                        'row': row_idx,
                        'col': col_idx,
                        'x0': x0,
                        'y0': y0,
                        'x1': x1,
                        'y1': y1,
                        'width': x1 - x0,
                        'height': y1 - y0
                    })
            
            print(f"  Created {len(self.cells)} cells from line intersections")
    
    def visualize_cells(self, output_path: str):
        """
        Create a visual representation of detected cells.
        
        Args:
            output_path: Path to save visualization image
        """
        print(f"\nCreating visualization...")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            page = pdf.pages[0]
            
            # Convert PDF page to image
            img = page.to_image(resolution=150)
            
            # Draw rectangles around each detected cell
            for i, cell in enumerate(self.cells):
                # Color code by row for easier viewing
                color_map = [
                    "red", "blue", "green", "purple", "orange", 
                    "cyan", "magenta", "yellow", "pink", "brown"
                ]
                row_color = color_map[cell['row'] % len(color_map)]
                
                # Draw the cell boundary
                bbox_tuple = (cell['x0'], cell['y0'], cell['x1'], cell['y1'])
                img.draw_rect(bbox_tuple, stroke=row_color, stroke_width=1)
            
            # Save the image
            img.save(output_path)
            print(f"  ✓ Saved visualization to: {output_path}")
    
    def export_cell_info(self, output_csv: str):
        """
        Export cell coordinates to CSV for inspection.
        
        Args:
            output_csv: Path to save CSV file
        """
        if not self.cells:
            print("No cells detected yet. Run detect_cells() first.")
            return
        
        df = pd.DataFrame(self.cells)
        df.to_csv(output_csv, index=False)
        print(f"  ✓ Exported cell info to: {output_csv}")
    
    def get_cell_grid_info(self):
        """Get information about the detected grid structure."""
        if not self.cells:
            return None
        
        df = pd.DataFrame(self.cells)
        
        max_row = df['row'].max()
        max_col = df['col'].max()
        
        # Get some statistics
        avg_cell_width = df['width'].mean()
        avg_cell_height = df['height'].mean()
        
        info = {
            'total_cells': len(self.cells),
            'rows': max_row + 1,
            'cols': max_col + 1,
            'avg_cell_width': avg_cell_width,
            'avg_cell_height': avg_cell_height,
            'min_x': df['x0'].min(),
            'max_x': df['x1'].max(),
            'min_y': df['y0'].min(),
            'max_y': df['y1'].max()
        }
        
        return info
    
    def print_grid_structure(self):
        """Print a summary of the detected grid."""
        info = self.get_cell_grid_info()
        
        if not info:
            print("No cells detected yet.")
            return
        
        print("\n" + "=" * 70)
        print("DETECTED GRID STRUCTURE")
        print("=" * 70)
        print(f"Total cells detected: {info['total_cells']}")
        print(f"Grid dimensions: {info['rows']} rows × {info['cols']} columns")
        print(f"Average cell size: {info['avg_cell_width']:.1f} × {info['avg_cell_height']:.1f}")
        print(f"Table bounds: ({info['min_x']:.1f}, {info['min_y']:.1f}) to ({info['max_x']:.1f}, {info['max_y']:.1f})")
        print("=" * 70)
        
        # Show some sample cells
        print("\nSample cells (first 20):")
        print(f"{'Row':>4} {'Col':>4} {'X0':>7} {'Y0':>7} {'X1':>7} {'Y1':>7} {'Width':>7} {'Height':>7}")
        print("-" * 70)
        for cell in self.cells[:20]:
            print(f"{cell['row']:4d} {cell['col']:4d} "
                  f"{cell['x0']:7.1f} {cell['y0']:7.1f} {cell['x1']:7.1f} {cell['y1']:7.1f} "
                  f"{cell['width']:7.1f} {cell['height']:7.1f}")
    
    def extract_text_from_cell(self, row: int, col: int) -> str:
        """
        Extract text from a specific cell.
        
        Args:
            row: Row index
            col: Column index
            
        Returns:
            Text content of the cell
        """
        # Find the cell
        cell = next((c for c in self.cells if c['row'] == row and c['col'] == col), None)
        
        if not cell:
            return ""
        
        # Extract text within this cell's bounding box
        with pdfplumber.open(self.pdf_path) as pdf:
            page = pdf.pages[0]
            
            # Crop to cell area (with small margins to avoid border issues)
            bbox = (
                cell['x0'] + 1,
                cell['y0'] + 1,
                cell['x1'] - 1,
                cell['y1'] - 1
            )
            
            cropped = page.within_bbox(bbox)
            text = cropped.extract_text()
            
            return text.strip() if text else ""
    
    def sample_cell_extraction(self, num_samples: int = 10):
        """
        Sample some cells and show their extracted text.
        
        Args:
            num_samples: Number of cells to sample
        """
        print(f"\n" + "=" * 70)
        print(f"SAMPLING {num_samples} CELLS")
        print("=" * 70)
        
        # Sample cells from different rows
        sampled_rows = list(range(0, min(5, max(c['row'] for c in self.cells) + 1)))
        
        for row in sampled_rows:
            # Get first few cells in this row
            row_cells = [c for c in self.cells if c['row'] == row][:5]
            
            print(f"\nRow {row}:")
            for cell in row_cells:
                text = self.extract_text_from_cell(cell['row'], cell['col'])
                text_display = repr(text)[:40] if text else "(empty)"
                print(f"  Col {cell['col']:2d}: {text_display}")



def main():
    """Run cell detection and visualization."""
    
    print("=" * 80)
    print("PDF TABLE CELL DETECTOR & VISUALIZER")
    print("=" * 80)
    
    pdf_path = "./pdfs/Januari Rooster Den Helder 2026.pdf"

    # Create detector
    detector = CellDetector(pdf_path)
    
    # Step 1: Detect cells
    print("\n[STEP 1] Detecting cells...")
    cells = detector.detect_cells()
    
    # Step 2: Print grid structure
    print("\n[STEP 2] Analyzing grid structure...")
    detector.print_grid_structure()
    
    # Step 3: Sample some cells
    print("\n[STEP 3] Sampling cell content...")
    detector.sample_cell_extraction(num_samples=15)
    
    # Step 4: Create visualization
    print("\n[STEP 4] Creating visualization...")
    vis_path = "./outputs/cell_detection_visual4.png"
    detector.visualize_cells(vis_path)
    
    # Step 5: Export cell coordinates
    print("\n[STEP 5] Exporting cell coordinates...")
    csv_path = "./outputs/cell_coordinates4.csv"
    detector.export_cell_info(csv_path)
    
    print("\n" + "=" * 80)
    print("✅ CELL DETECTION COMPLETE")
    print("=" * 80)
    print(f"\nPlease review:")
    print(f"  1. Visual overlay: {vis_path}")
    print(f"  2. Cell coordinates: {csv_path}")
    print("\nIf the cells look correct, we can proceed with extraction!")
    print("=" * 80)
    
    return detector


if __name__ == "__main__":
    detector = main()