# UPAS Data Processor

A Python tool for processing and analyzing UPAS (Ultrasonic Personal Air Sampler) data files, automatically extracting participant IDs, timestamps, and organizing air quality measurements for research analysis.


## 📋 Overview

The UPAS Data Processor extracts, consolidates, and organizes data from UPAS air quality monitoring devices. It takes individual text files containing air quality measurements and combines them into structured datasets, extracting important metadata like participant IDs and timestamps from filenames.

### Key Features

- **Automated File Processing**: Recursively processes all UPAS data files in a directory structure
- **Metadata Extraction**: Extracts participant IDs and timestamps from filenames
- **Dual Dataset Creation**: Creates separate datasets for device properties and time-series measurements
- **Original Column Order Preservation**: Maintains the original structure of data files
- **Comprehensive Error Handling**: Logs issues while continuing to process other files
- **Progress Tracking**: Shows real-time processing status with completion estimates

## 🔍 How It Works

### In Simple Terms

The program:
1. Finds all UPAS data files in a folder (and its subfolders)
2. Extracts participant IDs and timestamps from filenames
3. Opens each file and carefully extracts two types of information:
   - Device properties and settings
   - Actual air quality measurements
4. Combines all this information from multiple files into two clean datasets
5. Preserves the original column order from the data files
6. Adds file path, participant ID, and timestamp to each row
7. Saves the combined data as CSV files for easy analysis

### Technical Details

The processor follows this algorithm:

1. **File Discovery**
   - Recursively walks through the specified directory
   - Identifies all `.txt` files

2. **Filename Analysis**
   - Extracts participant ID (mstudyid) using regex patterns
   - Extracts timestamp (filedate) from the filename

3. **File Parsing**
   - Attempts to open each file with multiple encodings (UTF-8, Latin-1, etc.) for compatibility
   - Locates the "SAMPLE LOG" marker that separates properties from sample data
   - Parses properties section into key-value pairs with units
   - Extracts column headers from the sample data section
   - Processes data rows, handling potential inconsistencies
   - Adds file path, participant ID, and timestamp as the first columns

4. **Data Combination**
   - Preserves the original column order from the input files
   - Adds any missing columns discovered in later files
   - Reconciles column differences between files
   - Concatenates all data into unified datasets

5. **Error Handling**
   - Logs errors with file-specific details
   - Continues processing despite individual file failures
   - Provides a summary of successful and failed operations

## 📊 Output Files

The processor generates several files in the output directory:

- `combined_properties.csv` - All device metadata and settings
- `combined_data.csv` - All measurement data from all files
- `summary.txt` - Overview of processing results
- `error_log.txt` - Details of any errors encountered

Both CSV files include:
- FILEPATH: Location of the original file
- mstudyid: Participant ID extracted from filename
- filedate: Date and time extracted from filename

## 🚀 Installation

```bash
# Clone this repository
git clone https://github.com/agyeioscarkhrc/upas-data-processor.git

# Change into the repository directory
cd upas-data-processor

# Install required dependencies
pip install -r requirements.txt

pip install pandas tqdm
```

## 📖 Usage

### Command Line

```bash
python process_upas_data.py --data_folder "UPAS DATA" --output_dir "processed_data"
```

### Python Script

```python
from upas_processor import process_upas_files

data_folder = "UPAS DATA"  # Path to your UPAS data folder
output_dir = "processed_data"

properties_df, data_df = process_upas_files(data_folder, output_dir)
```

### Jupyter Notebook

To run the processor in a Jupyter Notebook:

1. Install prerequisites:
   ```python
   !pip install pandas tqdm
   ```

2. Import and run the processor:
   ```python
   from upas_processor import process_upas_files
   
   data_folder = "UPAS DATA"  # Update this path to your actual data folder
   output_dir = "processed_data"
   
   print(f"Starting processing of UPAS data from {data_folder}")
   properties_df, data_df = process_upas_files(data_folder, output_dir)
   print(f"Processing complete. Results saved to {output_dir}")
   
   # Open the output folder automatically
   open_output_folder(output_dir)
   
   # View the results
   print("Sample of properties data:")
   properties_df.head()
   
   print("Sample of time-series data:")
   data_df.head()
   ```

## 💡 Why This Matters

This automated process:
- Saves hours of manual data extraction
- Ensures consistency in how files are processed
- Reduces the chance of human error
- Makes it easy to identify which data belongs to which participant
- Allows for time-based analysis of the collected data

By automatically extracting participant IDs and timestamps, user can immediately begin analyzing patterns and relationships without spending time on data preparation.

## 📝 Example File Structure

```
UPAS DATA/
├── 20241222/
│   ├── PSP00006_LOG_2024-12-20T10_12_01UTC_BM0457M_________DUMMY_____.txt
│   └── [more files...]
├── 20241226/ 
│   └── [files...]
└── [more folders...]
```

## 🔧 Troubleshooting

- **File encoding issues**: The processor attempts multiple encodings, but you may need to add more if you encounter persistent errors
- **Memory errors**: If processing large datasets, consider increasing available memory or processing files in batches
- **Missing participant IDs**: Check that your filenames follow the expected format with participant IDs

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is for KHRC.

## 🔍 Example Data Format

### Properties Table Format
| FILEPATH | mstudyid | filedate | PARAMETER | VALUE | UNITS/NOTES |
|----------|----------|----------|-----------|-------|-------------|
| path/to/file.txt | BM0457M | 2024-12-20T10:12:01 | SERIAL NUMBER | PSP00006 | - |
| path/to/file.txt | BM0457M | 2024-12-20T10:12:01 | START TIME | 2024-12-20T10:12:01 | UTC |

### Data Table Format
| FILEPATH | mstudyid | filedate | SampleTime | DateTimeUTC | PM2_5MC | ... |
|----------|----------|----------|------------|-------------|---------|-----|
| path/to/file.txt | BM0457M | 2024-12-20T10:12:01 | 60 | 2024-12-20T10:13:01 | 12.5 | ... |
| path/to/file.txt | BM0457M | 2024-12-20T10:12:01 | 120 | 2024-12-20T10:14:01 | 13.2 | ... |
