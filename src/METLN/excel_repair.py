"""
Utility to repair and read corrupted Excel files
"""
import pandas as pd
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import logging


def extract_data_from_corrupted_xlsx(file_path):
    """
    Manually extract data from a corrupted .xlsx file by reading the XML directly.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        pandas DataFrame with the data
    """
    logging.info(f"Attempting manual extraction for {file_path}")
    
    try:
        # xlsx files are zip archives
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # Read shared strings (if any)
            shared_strings = []
            try:
                with zip_ref.open('xl/sharedStrings.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    # Excel uses multiple possible namespaces for shared strings
                    namespaces = [
                        {'ss': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'},
                        {'ss': 'http://purl.oclc.org/ooxml/spreadsheetml/main'}
                    ]
                    
                    # Try different namespaces
                    for ns in namespaces:
                        si_elements = root.findall('.//ss:si', ns)
                        if si_elements:
                            for si in si_elements:
                                t = si.find('.//ss:t', ns)
                                if t is not None:
                                    shared_strings.append(t.text if t.text else '')
                                else:
                                    shared_strings.append('')
                            logging.info(f"Found {len(shared_strings)} shared strings")
                            break
            except KeyError:
                logging.info("No shared strings found")
            
            # Find the first worksheet
            sheet_files = [f for f in zip_ref.namelist() if f.startswith('xl/worksheets/sheet')]
            if not sheet_files:
                raise ValueError("No worksheet found in the Excel file")
            
            # Read the first sheet
            with zip_ref.open(sheet_files[0]) as f:
                tree = ET.parse(f)
                root = tree.getroot()
                
                # Excel uses multiple possible namespaces
                namespaces = {
                    'ss': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
                    'ss2': 'http://purl.oclc.org/ooxml/spreadsheetml/main'
                }
                
                # Try to find sheetData with different namespaces
                sheet_data = None
                for ns_key, ns_val in namespaces.items():
                    sheet_data = root.find(f'.//{{{ns_val}}}sheetData')
                    if sheet_data is not None:
                        ns = {ns_key: ns_val}
                        logging.info(f"Found sheetData using namespace: {ns_val}")
                        break
                
                if sheet_data is None:
                    raise ValueError("No sheetData element found in worksheet")
                
                # Extract all rows
                rows_data = []
                for row in sheet_data.findall(f'.//{{{ns[ns_key]}}}row'):
                    row_data = []
                    cells = row.findall(f'.//{{{ns[ns_key]}}}c')
                    
                    # Track cell references to handle missing cells
                    for cell in cells:
                        value = cell.find(f'.//{{{ns[ns_key]}}}v')
                        cell_type = cell.get('t', 'n')  # 'n' for number, 's' for shared string, 'd' for date
                        
                        if value is not None:
                            if cell_type == 's':  # Shared string
                                idx = int(value.text)
                                if idx < len(shared_strings):
                                    row_data.append(shared_strings[idx])
                                else:
                                    row_data.append(value.text)
                            else:
                                row_data.append(value.text)
                        else:
                            row_data.append(None)
                    
                    if row_data:  # Only add non-empty rows
                        rows_data.append(row_data)
                
                if not rows_data:
                    raise ValueError("No data found in worksheet")
                
                # First row as headers
                headers = rows_data[0] if rows_data else []
                data_rows = rows_data[1:] if len(rows_data) > 1 else []
                
                # Make sure all rows have the same length
                max_cols = max(len(row) for row in rows_data) if rows_data else 0
                for row in data_rows:
                    while len(row) < max_cols:
                        row.append(None)
                
                # Create DataFrame
                df = pd.DataFrame(data_rows, columns=headers if len(headers) == max_cols else None)
                logging.info(f"Successfully extracted {len(df)} rows and {len(df.columns)} columns")
                
                return df
                
    except Exception as e:
        logging.error(f"Failed to manually extract data: {e}")
        raise
