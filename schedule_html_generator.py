import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import List, Dict


def generate_schedule_html(
    dest_path: str,
    output_file: str = "schedule.html",
    start_date: str = None
) -> str:
    """
    Generate an interactive HTML schedule viewer.
    
    Args:
        dest_path: Path to folder containing extracted CSV schedules
        output_file: Output HTML filename
        start_date: Optional start date (YYYY-MM-DD). Defaults to current week.
    
    Returns:
        Path to generated HTML file
    """
    print("Reading schedule files...")
    
    # Read all CSV files and combine them
    csv_files = list(Path(dest_path).glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in {dest_path}")
    
    print(f"Found {len(csv_files)} schedule files")
    
    # Combine all schedules
    all_schedules = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            if not df.empty:
                # Extract location from filename
                # Format: sam_schedule_2026_01_Januari_Den_Helder.csv
                filename = csv_file.stem
                if "Den_Helder" in filename:
                    location = "Den Helder"
                elif "Alkmaar" in filename:
                    location = "Alkmaar"
                else:
                    location = "Unknown"
                
                df['Location'] = location
                all_schedules.append(df)
                print(f"  Loaded {len(df)} records from {csv_file.name} ({location})")
        except Exception as e:
            print(f"Warning: Could not read {csv_file.name}: {e}")
    
    if not all_schedules:
        raise ValueError("No valid schedule data found")
    
    combined_df = pd.concat(all_schedules, ignore_index=True)
    print(f"Total records loaded: {len(combined_df)}")
    
    # Convert Date column to datetime
    combined_df['Date'] = pd.to_datetime(combined_df['Date'])
    
    # Sort by date
    combined_df = combined_df.sort_values('Date')
    
    # Prepare data for JavaScript
    schedule_data = prepare_schedule_data(combined_df)
    
    # Generate HTML
    html_content = generate_html_content(schedule_data, start_date)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ HTML schedule generated: {output_file}")
    return output_file


def prepare_schedule_data(df: pd.DataFrame) -> List[Dict]:
    """Convert DataFrame to list of dictionaries for JavaScript."""
    records = []
    for _, row in df.iterrows():
        # Only include rows that have a shift (Shift column is not empty/NaN)
        shift_value = str(row.get('Shift', '')).strip()
        
        # Skip if no shift scheduled (empty or NaN)
        if not shift_value or shift_value == 'nan':
            continue
            
        record = {
            'date': row['Date'].strftime('%Y-%m-%d'),
            'day_of_week': row['Date'].strftime('%A'),
            'employee': row.get('Employee', 'Sam'),
            'role': str(row.get('Role', '')),
            'location': row.get('Location', 'Unknown'),
            'shift': shift_value
        }
        records.append(record)
    return records


def generate_html_content(schedule_data: List[Dict], start_date: str = None) -> str:
    """Generate the complete HTML content."""
    
    # Convert schedule data to JSON for embedding
    schedule_json = json.dumps(schedule_data, indent=2)
    
    # Determine initial date (current Monday or specified date)
    if start_date:
        initial_date = start_date
    else:
        today = datetime.now()
        # Get Monday of current week
        monday = today - timedelta(days=today.weekday())
        initial_date = monday.strftime('%Y-%m-%d')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sam's Work Schedule</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        .week-navigator {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .week-info {{
            font-size: 18px;
            font-weight: 600;
            color: #495057;
            flex: 1;
            text-align: center;
            min-width: 250px;
        }}
        
        .nav-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            background: #667eea;
            color: white;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: background 0.3s;
        }}
        
        .btn:hover {{
            background: #5568d3;
        }}
        
        .btn:active {{
            transform: scale(0.98);
        }}
        
        .locations-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            padding: 30px;
        }}
        
        .location-section {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
        }}
        
        .location-title {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 20px;
            color: #667eea;
            text-align: center;
        }}
        
        .day-card {{
            background: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }}
        
        .day-card.no-shift {{
            opacity: 0.5;
            border-left-color: #dee2e6;
        }}
        
        .day-card.current-day {{
            border-left-width: 6px;
            border-left-color: #28a745;
            background: #f0fff4;
            box-shadow: 0 2px 8px rgba(40, 167, 69, 0.2);
        }}
        
        .day-card.current-day .day-name {{
            color: #28a745;
        }}
        
        .current-day-badge {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 8px;
        }}
        
        .day-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .day-name {{
            font-weight: 700;
            font-size: 16px;
            color: #495057;
        }}
        
        .day-date {{
            font-size: 14px;
            color: #6c757d;
        }}
        
        .shift-info {{
            margin-top: 8px;
        }}
        
        .shift-time {{
            font-size: 18px;
            font-weight: 600;
            color: #212529;
            margin-bottom: 5px;
        }}
        
        .shift-details {{
            font-size: 14px;
            color: #6c757d;
        }}
        
        .shift-description {{
            font-size: 13px;
            color: #495057;
            margin-top: 4px;
            font-style: italic;
        }}
        
        .btn-secondary {{
            background: #6c757d;
        }}
        
        .btn-secondary:hover {{
            background: #5a6268;
        }}
        
        .btn-success {{
            background: #28a745;
        }}
        
        .btn-success:hover {{
            background: #218838;
        }}
        
        .no-shift-message {{
            color: #6c757d;
            font-style: italic;
        }}
        
        .empty-week {{
            text-align: center;
            padding: 40px;
            color: #6c757d;
            font-size: 16px;
        }}
        
        @media (max-width: 768px) {{
            .locations-container {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}
            
            .week-navigator {{
                flex-direction: column;
                gap: 15px;
            }}
            
            .nav-buttons {{
                width: 100%;
                justify-content: center;
            }}
            
            .week-info {{
                order: -1;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 Sam's Work Schedule</h1>
            <p>Weekly Overview - Both Locations</p>
        </div>
        
        <div class="week-navigator">
            <button class="btn" onclick="previousWeek()">← Previous Week</button>
            <div class="week-info" id="weekInfo">Loading...</div>
            <div class="nav-buttons">
                <button class="btn btn-success" onclick="goToCurrentWeek()">Current Week</button>
                <button class="btn btn-secondary" onclick="toggleShiftInfo()" id="shiftInfoBtn">Show Shift Info</button>
                <button class="btn" onclick="nextWeek()">Next Week →</button>
            </div>
        </div>
        
        <div class="locations-container" id="scheduleContainer">
            <!-- Schedule will be populated by JavaScript -->
        </div>
    </div>

    <script>
        // Embedded schedule data
        const scheduleData = {schedule_json};
        
        // Current week start date (Monday)
        let currentWeekStart = new Date('{initial_date}');
        
        // Shift info toggle
        let showShiftInfo = false;
        
        // Shift descriptions mapping
        const shiftDescriptions = {{
            'N': 'Nachtdienst',
            'n': 'Nachtdienst',
            'D': 'Dagdienst',
            'd': 'Dagdienst',
            'A': 'Avonddienst',
            'a': 'Avonddienst',
            '-': 'Free?',
            'x': 'Vrijgevraagd',
            'X': 'Vrijgevraagd'
        }};
        
        // Parse schedule data and create lookup
        const scheduleByDate = {{}};
        scheduleData.forEach(item => {{
            if (!scheduleByDate[item.date]) {{
                scheduleByDate[item.date] = {{}};
            }}
            scheduleByDate[item.date][item.location] = item;
        }});
        
        function getMonday(date) {{
            const d = new Date(date);
            const day = d.getDay();
            const diff = d.getDate() - day + (day === 0 ? -6 : 1);
            return new Date(d.setDate(diff));
        }}
        
        function formatDate(date) {{
            const options = {{ year: 'numeric', month: 'long', day: 'numeric' }};
            return date.toLocaleDateString('en-US', options);
        }}
        
        function formatDateShort(date) {{
            const options = {{ month: 'short', day: 'numeric' }};
            return date.toLocaleDateString('en-US', options);
        }}
        
        function getDateString(date) {{
            return date.toISOString().split('T')[0];
        }}
        
        function isToday(date) {{
            const today = new Date();
            return date.getDate() === today.getDate() &&
                   date.getMonth() === today.getMonth() &&
                   date.getFullYear() === today.getFullYear();
        }}
        
        function getShiftDisplay(shiftCode) {{
            if (!showShiftInfo || !shiftDescriptions[shiftCode]) {{
                return `Shift: ${{shiftCode}}`;
            }}
            return `Shift: ${{shiftCode}} (${{shiftDescriptions[shiftCode]}})`;
        }}
        
        function toggleShiftInfo() {{
            showShiftInfo = !showShiftInfo;
            const btn = document.getElementById('shiftInfoBtn');
            btn.textContent = showShiftInfo ? 'Hide Shift Info' : 'Show Shift Info';
            renderSchedule();
        }}
        
        function goToCurrentWeek() {{
            const today = new Date();
            currentWeekStart = getMonday(today);
            renderSchedule();
        }}
        
        function renderSchedule() {{
            const monday = getMonday(currentWeekStart);
            const sunday = new Date(monday);
            sunday.setDate(sunday.getDate() + 6);
            
            // Update week info
            document.getElementById('weekInfo').textContent = 
                `${{formatDate(monday)}} - ${{formatDate(sunday)}}`;
            
            // Render both locations
            const locations = ['Den Helder', 'Alkmaar'];
            const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
            
            let html = '';
            
            locations.forEach(location => {{
                html += `
                    <div class="location-section">
                        <div class="location-title">${{location}}</div>
                        <div class="days-container">
                `;
                
                let hasAnyShifts = false;
                
                for (let i = 0; i < 7; i++) {{
                    const date = new Date(monday);
                    date.setDate(date.getDate() + i);
                    const dateStr = getDateString(date);
                    const dayName = daysOfWeek[i];
                    const today = isToday(date);
                    
                    const shift = scheduleByDate[dateStr]?.[location];
                    
                    if (shift) {{
                        hasAnyShifts = true;
                        html += `
                            <div class="day-card${{today ? ' current-day' : ''}}">
                                <div class="day-header">
                                    <div class="day-name">
                                        ${{dayName}}
                                        ${{today ? '<span class="current-day-badge">TODAY</span>' : ''}}
                                    </div>
                                    <div class="day-date">${{formatDateShort(date)}}</div>
                                </div>
                                <div class="shift-info">
                                    <div class="shift-time">${{getShiftDisplay(shift.shift)}}</div>
                                    <div class="shift-details">
                                        ${{shift.role ? shift.role : ''}}
                                    </div>
                                </div>
                            </div>
                        `;
                    }} else {{
                        html += `
                            <div class="day-card no-shift${{today ? ' current-day' : ''}}">
                                <div class="day-header">
                                    <div class="day-name">
                                        ${{dayName}}
                                        ${{today ? '<span class="current-day-badge">TODAY</span>' : ''}}
                                    </div>
                                    <div class="day-date">${{formatDateShort(date)}}</div>
                                </div>
                                <div class="no-shift-message">No shift scheduled</div>
                            </div>
                        `;
                    }}
                }}
                
                if (!hasAnyShifts) {{
                    html += '<div class="empty-week">No shifts scheduled for this week</div>';
                }}
                
                html += `
                        </div>
                    </div>
                `;
            }});
            
            document.getElementById('scheduleContainer').innerHTML = html;
        }}
        
        function previousWeek() {{
            currentWeekStart.setDate(currentWeekStart.getDate() - 7);
            renderSchedule();
        }}
        
        function nextWeek() {{
            currentWeekStart.setDate(currentWeekStart.getDate() + 7);
            renderSchedule();
        }}
        
        // Initial render
        renderSchedule();
    </script>
</body>
</html>"""
    
    return html


if __name__ == "__main__":
    # Example usage
    generate_schedule_html(
        dest_path="./extracted_schedules/",
        output_file="./docs/index.html"
    )