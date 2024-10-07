import pandas as pd
import re

# Function to read addresses from a CSV file
def read_addresses_from_csv(csv_file_path):
    try:
        df = pd.read_csv(csv_file_path, sep=',', encoding='utf-8', on_bad_lines='skip')  
    except UnicodeDecodeError:
        df = pd.read_csv(csv_file_path, sep=',', encoding='latin1', on_bad_lines='skip')  
    
    
    print("CSV Columns:", df.columns)
    
    
    address_column = next((col for col in df.columns if col.strip().lower() == 'address'), None)
    
    if address_column is None:
        raise KeyError("The 'Address' column was not found in the CSV file.")
    
    # Extract addresses along with their first four digits
    return {address: extract_first_four_digits(address) for address in df[address_column].dropna()}

# Function to read addresses from a TXT file
def read_addresses_from_txt(txt_file_path):
    addresses = {}
    with open(txt_file_path, 'r') as file:
        for line in file:
            match = re.search(r"Address: (.*?)(,|$)", line)
            if match:
                address = match.group(1).strip().lower()  
                first_four_digits = extract_first_four_digits(address)
                if first_four_digits:
                    addresses[address] = first_four_digits
    return addresses

# Function to extract the first four digits of an address
def extract_first_four_digits(address):
    match = re.search(r'\d{4}', address) 
    return match.group(0) if match else None

# Function to compare addresses
def compare_addresses(csv_file_path, txt_file_path):
    csv_addresses = read_addresses_from_csv(csv_file_path)
    txt_addresses = read_addresses_from_txt(txt_file_path)

    # Create sets based on the first four digits
    csv_keys = {v for v in csv_addresses.values()}
    txt_keys = {v for v in txt_addresses.values()}

    # Find matches and differences
    matches = {k: v for k, v in csv_addresses.items() if v in txt_keys}
    only_in_csv = {k: v for k, v in csv_addresses.items() if v not in txt_keys}
    only_in_txt = {k: v for k, v in txt_addresses.items() if v not in csv_keys}

    return matches, only_in_csv, only_in_txt

# File paths
csv_file_path = 'C:/Users/aidan/Downloads/checker/louisville.csv'  
txt_file_path = 'C:/Users/aidan/Downloads/checker/results.txt'  

# Perform comparison
matches, only_in_csv, only_in_txt = compare_addresses(csv_file_path, txt_file_path)

# Output results
print(f"Matching addresses (first 4 digits):\n{matches}\nCount: {len(matches)}\n")
print(f"Addresses only in CSV (first 4 digits):\n{only_in_csv}\nCount: {len(only_in_csv)}\n")
print(f"Addresses only in TXT (first 4 digits):\n{only_in_txt}\nCount: {len(only_in_txt)}\n")
