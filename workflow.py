#!/usr/bin/env python
# coding: utf-8

import os
import pandas as pd
import re
import traceback
from tqdm import tqdm
import datetime
import argparse

pd.set_option('display.max_columns', None)

def get_file_list(data_folder):
    """Get a list of all files in the data folder and its subfolders."""
    return [os.path.join(dirpath, file).replace(os.path.sep, '/') 
            for dirpath, dirnames, files in os.walk(data_folder) 
            for file in files if file.endswith('.txt')]

def open_output_folder(folder_path):
    """Open the output folder in the system's file explorer"""
    import os
    import platform
    import subprocess
    
    folder_path = os.path.abspath(folder_path)
    
    if platform.system() == "Windows":
        # For Windows
        os.startfile(folder_path)
    elif platform.system() == "Darwin":
        # For macOS
        subprocess.Popen(["open", folder_path])
    else:
        # For Linux
        subprocess.Popen(["xdg-open", folder_path])

def extract_info_from_filename(file_path):
    """
    Extract mstudyid and filedate from the filename.
    
    Returns:
    - mstudyid: Participant ID (e.g., BM0457M)
    - filedate: File date in datetime format
    """
    filename = os.path.basename(file_path)
    
    # Extract mstudyid using regex
    # Pattern looks for section after UTC_ and before _DUMMY
    mstudyid_match = re.search(r'UTC_([A-Za-z0-9]+)_+DUMMY', filename)
    mstudyid = mstudyid_match.group(1) if mstudyid_match else "Unknown"
    
    # Extract filedate using regex
    # Pattern looks for date format like 2024-12-20T10_12_01
    filedate_str_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2})', filename)
    filedate_str = filedate_str_match.group(1) if filedate_str_match else None
    
    # Convert filedate string to datetime object
    filedate = None
    if filedate_str:
        try:
            # Replace underscores with colons in the time part
            formatted_str = filedate_str.replace('_', ':')
            filedate = pd.to_datetime(formatted_str)
        except:
            pass
    
    return mstudyid, filedate_str, filedate

def parse_upas_file(file_path):
    """
    Parse UPAS data file into two dataframes with error handling.
    Returns:
    - properties_df: Contains metadata with "PARAMETER", "VALUE", "UNITS/NOTES" columns
    - data_df: Contains sample log data
    - error: Error message if any
    """
    # Extract mstudyid and filedate from filename
    mstudyid, filedate_str, filedate = extract_info_from_filename(file_path)
    
    # Try different encodings
    encodings = ['utf-8', 'latin1', 'cp1252', 'ISO-8859-1']
    lines = None
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            break  # If successful, exit the loop
        except Exception as e:
            continue  # Try the next encoding
    
    if lines is None:
        return None, None, f"Failed to decode file with any of the attempted encodings"
        
    try:
        # Find the line index where "SAMPLE LOG" appears
        sample_log_index = None
        for i, line in enumerate(lines):
            if "SAMPLE LOG" in line:
                sample_log_index = i
                break
        
        if sample_log_index is None:
            return None, None, "Could not find 'SAMPLE LOG' marker in file"
        
        # Parse properties
        properties_data = []
        
        # Skip first line and read until SAMPLE LOG
        for line in lines[1:sample_log_index]:
            line = line.strip()
            # Skip empty lines and section headers (all capital letters with no commas)
            if not line or "," not in line or (line.isupper() and "," not in line):
                continue
            
            # Extract parts using regex to handle parentheses in comments properly
            parts = re.split(r',([^,(]*(?:\([^)]*\)[^,]*)*)', line, 1)
            
            if len(parts) >= 2:
                parameter = parts[0].strip()
                value = parts[1].strip()
                
                # Extract units/notes (everything after the second comma)
                units_notes = ""
                if len(parts) > 2 and parts[2]:
                    units_notes = parts[2].strip()
                    # Remove leading comma if present
                    if units_notes.startswith(','):
                        units_notes = units_notes[1:].strip()
                
                properties_data.append({
                    "FILEPATH": file_path,
                    "mstudyid": mstudyid,
                    "filedate": filedate,
                    "PARAMETER": parameter,
                    "VALUE": value,
                    "UNITS/NOTES": units_notes
                })
        
        # Create properties DataFrame
        properties_df = pd.DataFrame(properties_data)
        
        # Parse data
        # The header is 3 lines after SAMPLE LOG
        header_index = sample_log_index + 3
        if header_index >= len(lines):
            return properties_df, None, "File format error: header line not found after SAMPLE LOG"
        
        header = lines[header_index].strip().split(',')
        
        # Skip the units line
        data_start_index = header_index + 2
        
        # Process data lines
        data_content = []
        for line in lines[data_start_index:]:
            line = line.strip()
            if not line or line.startswith('-----'):
                continue  # Skip separator lines or empty lines
            
            values = line.split(',')
            if len(values) > 1:  # Ensure it's a data line
                # If there are fewer values than headers, pad with NaN
                if len(values) < len(header):
                    values.extend([''] * (len(header) - len(values)))
                # If there are more values than headers, truncate
                elif len(values) > len(header):
                    values = values[:len(header)]
                    
                data_content.append(values)
        
        # Create data DataFrame
        if data_content:
            data_df = pd.DataFrame(data_content, columns=header)
            # Add filepath and extracted info columns at the beginning
            data_df.insert(0, 'FILEPATH', file_path)
            data_df.insert(1, 'mstudyid', mstudyid)
            data_df.insert(2, 'filedate', filedate)
        else:
            # Create empty DataFrame with FILEPATH, mstudyid, and filedate as first columns
            columns = ['FILEPATH', 'mstudyid', 'filedate'] + header
            data_df = pd.DataFrame(columns=columns)
        
        return properties_df, data_df, None
        
    except Exception as e:
        error_detail = traceback.format_exc()
        return None, None, f"Error: {str(e)}\n{error_detail}"

def log_error(output_dir, error_message, file_path):
    """Log errors to a file"""
    os.makedirs(output_dir, exist_ok=True)
    error_log_path = os.path.join(output_dir, "error_log.txt")
    
    with open(error_log_path, 'a') as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {os.path.basename(file_path)}: {error_message}\n")
        f.write("-" * 80 + "\n")

def process_upas_files(data_folder, output_dir="output", open_folder=True):
    """
    Process all UPAS files in the data folder and combine the results.
    Saves results to CSV files and returns the combined dataframes.
    
    Args:
        data_folder (str): Path to the folder containing UPAS data files
        output_dir (str): Path where output CSV files will be saved
        open_folder (bool): Whether to open the output folder after processing
        
    Returns:
        tuple: (properties_df, data_df) containing the combined data
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get file list
    file_list = get_file_list(data_folder)
    total_files = len(file_list)
    
    if total_files == 0:
        print(f"No .txt files found in the specified data folder: {data_folder}")
        return pd.DataFrame(), pd.DataFrame()
    
    # Prepare data containers
    all_properties = []
    all_data = []
    success_count = 0
    error_count = 0
    
    # Track original column order from first valid file
    original_columns = None
    
    # Process files with progress bar
    with tqdm(total=total_files, desc="Processing files", unit="file", 
             bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}") as pbar:
        
        for file_path in file_list:
            try:
                prop_df, data_df, error = parse_upas_file(file_path)
                
                if error:
                    error_count += 1
                    pbar.set_postfix_str(f"Success: {success_count}, Errors: {error_count}")
                    log_error(output_dir, f"Error processing {file_path}: {error}", file_path)
                else:
                    success_count += 1
                    if prop_df is not None:
                        all_properties.append(prop_df)
                    if data_df is not None:
                        # If this is the first valid dataframe, capture original column order
                        if original_columns is None and not data_df.empty:
                            # Get all columns except our added columns which we'll place at the beginning
                            original_data_columns = [col for col in data_df.columns 
                                                   if col not in ['FILEPATH', 'mstudyid', 'filedate']]
                            # Store the original order with our columns at the beginning
                            original_columns = ['FILEPATH', 'mstudyid', 'filedate'] + original_data_columns
                            
                        all_data.append(data_df)
                    pbar.set_postfix_str(f"Success: {success_count}, Errors: {error_count}")
            except Exception as e:
                error_count += 1
                error_detail = traceback.format_exc()
                pbar.set_postfix_str(f"Success: {success_count}, Errors: {error_count}")
                log_error(output_dir, f"Error processing {file_path}: {str(e)}\n{error_detail}", file_path)
            
            pbar.update(1)
    
    # Combine all dataframes
    if all_properties:
        combined_properties = pd.concat(all_properties, ignore_index=True)
        combined_properties.to_csv(os.path.join(output_dir, "combined_properties.csv"), index=False)
        print(f"Combined properties saved with {len(combined_properties)} rows")
    else:
        combined_properties = pd.DataFrame()
        print("No property data was successfully processed")
    
    if all_data:
        # Collect all unique columns from all dataframes
        all_columns = set()
        for df in all_data:
            all_columns.update(df.columns)
        
        # Make sure our important columns are first in the column list
        columns_to_use = ['FILEPATH', 'mstudyid', 'filedate']
        
        # If we have the original column order, use it
        if original_columns:
            # Add any original columns that aren't already in the list
            for col in original_columns:
                if col not in columns_to_use:
                    columns_to_use.append(col)
                    
            # Add any additional columns that weren't in the original order
            for col in sorted(all_columns):
                if col not in columns_to_use:
                    columns_to_use.append(col)
        else:
            # If we don't have original order, use alphabetical (after our important columns)
            columns_to_use.extend(sorted([col for col in all_columns 
                                        if col not in ['FILEPATH', 'mstudyid', 'filedate']]))
        
        # Ensure all dataframes have the same columns
        for i in range(len(all_data)):
            # Add missing columns
            for col in columns_to_use:
                if col not in all_data[i].columns:
                    all_data[i][col] = None
            
            # Reorder columns to match our desired order
            all_data[i] = all_data[i][columns_to_use]
        
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # Remove 'FILENAME' column if it exists (as in the original code)
        if 'FILENAME' in combined_data.columns:
            combined_data.drop(columns=['FILENAME'], inplace=True)
            
        combined_data.to_csv(os.path.join(output_dir, "combined_data.csv"), index=False)
        print(f"Combined data saved with {len(combined_data)} rows")
        
        # Print the columns to verify the order
        print("Columns in combined data:")
        print(combined_data.columns.tolist())
    else:
        combined_data = pd.DataFrame()
        print("No sample data was successfully processed")
    
    # Save summary
    with open(os.path.join(output_dir, "summary.txt"), 'w') as f:
        f.write(f"Total files processed: {total_files}\n")
        f.write(f"Successful: {success_count}\n")
        f.write(f"Errors: {error_count}\n")
        f.write(f"Properties rows: {len(combined_properties)}\n")
        f.write(f"Data rows: {len(combined_data)}\n")
    
    # Open the output folder if requested
    if open_folder:
        try:
            open_output_folder(output_dir)
        except Exception as e:
            print(f"Note: Could not open output folder automatically: {str(e)}")
    
    return combined_properties, combined_data

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Process UPAS data files into combined CSV files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python workflow.py --data_folder "UPAS DATA" --output_dir "processed_data"
  python workflow.py -d "UPAS DATA" -o "results" --no-open-folder
        '''
    )
    
    parser.add_argument('-d', '--data_folder', required=True,
                        help='Path to the folder containing UPAS data files')
    
    parser.add_argument('-o', '--output_dir', default="processed_data",
                        help='Path where output CSV files will be saved (default: processed_data)')
    
    parser.add_argument('--no-open-folder', action='store_true',
                        help='Do not open the output folder after processing')
    
    return parser.parse_args()

# Main execution
if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    print(f"Starting processing of UPAS data from {args.data_folder}")
    properties_df, data_df = process_upas_files(
        args.data_folder, 
        args.output_dir, 
        not args.no_open_folder  # Open folder unless --no-open-folder is specified
    )
    print(f"Processing complete. Results saved to {args.output_dir}")