import requests
import yaml
import pandas as pd
import logging
import re
from datetime import datetime
from fuzzywuzzy import fuzz, process

# Configure pandas
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.max_rows', None)     # Show all rows
pd.set_option('display.max_colwidth', None) # Show full column width for long text

# Configure logging
logging.basicConfig(
    filename='logs.txt', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Function to preprocess addresses by keeping building number, street name, and ZIP code
def preprocess_address(address):
    """
    Preprocess the address to keep only building number, street name, and ZIP code.
    """
    # Remove city and state; extract ZIP code
    match = re.search(r'(.*?),\s*LOUISVILLE,?\s*KY\s*(\d{5}(-\d{4})?)', address, flags=re.IGNORECASE)
    if match:
        street = match.group(1).strip()
        zip_code = match.group(2).strip()
        return f"{street} {zip_code}"  # Return as "street zip"
    return address  # Return the original if it doesn't match

# Function to read the queries and API key from the YAML file
def load_config_from_yaml(file_path):
    try:
        with open(file_path, 'r') as file:
            config_data = yaml.safe_load(file)
        queries_df = pd.DataFrame(config_data['queries'], columns=['keyword'])
        api_key = config_data['api_key']
        logging.info("Loaded config from YAML successfully")
        return api_key, queries_df
    except Exception as e:
        logging.error(f"Failed to load config from YAML: {e}")
        raise

# Use pandas to read coordinates from the CSV file
def load_coordinates_from_csv(file_path):
    try:
        coordinates_df = pd.read_csv(file_path)
        logging.info(f"Loaded {len(coordinates_df)} rectangles from CSV")
        return coordinates_df
    except Exception as e:
        logging.error(f"Failed to load coordinates from CSV: {e}")
        raise

# Function to get tobacco shops using Google Places API
def get_tobacco_shops(api_key, rectangles, queries_df):
    url = "https://places.googleapis.com/v1/places:searchText"
    
    results_list = []  # Initialize a list to collect results
    totals = []

    for rect_index, rectangle in rectangles.iterrows():
        inside_count = 0
        unique_place_ids = set()

        for _, row in queries_df.iterrows():
            query = row['keyword']
            payload = {
                "textQuery": query,
                "locationRestriction": {
                    "rectangle": {
                        "low": {
                            "latitude": rectangle["Low_Lat"],
                            "longitude": rectangle["Low_Lon"]
                        },
                        "high": {
                            "latitude": rectangle["High_Lat"],
                            "longitude": rectangle["High_Lon"]
                        }
                    }
                },
                "pageSize": 20
            }

            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': api_key,
                'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.id'
            }

            try:
                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status()  # Raise HTTPError for bad responses
                data = response.json()

                places = data.get('places', [])  # Retrieve places
                results_count = len(places)  # Get the number of results returned
                
                # Log a single message with box number and results count
                logging.info(f"Box {rect_index + 1}: Retrieved {results_count} results for query '{query}'")

                for place in places:
                    place_id = place.get('id')
                    display_name = place.get('displayName', {}).get('text', 'No name available')
                    formatted_address = place.get('formattedAddress', 'No address available')
                    
                    if place_id and place_id not in unique_place_ids:
                        unique_place_ids.add(place_id)
                        inside_count += 1
                        
                        # Collect the result in a list
                        results_list.append({
                            'Box': rect_index + 1,
                            'Keyword': query,
                            'Place Name': display_name,
                            'Address': formatted_address,
                            'Place ID': place_id  # Include Place ID in the results
                        })

            except requests.exceptions.RequestException as e:
                logging.error(f"Error making API request for query '{query}' in Box {rect_index + 1}: {e}")
            except Exception as e:
                logging.error(f"Unexpected error in Box {rect_index + 1}: {e}")

        totals.append(inside_count)

    # Convert the results list to a DataFrame at the end
    results_df = pd.DataFrame(results_list)
    
    # Capitalize the 'Address' field
    if not results_df.empty:
        results_df['Address'] = results_df['Address'].str.upper()  # Capitalize address
    
    return results_df, totals

# Function to filter results to include only Louisville, KY
def filter_louisville_results(results_df):
    try:
        logging.info(f"Starting filtering results for Louisville. Total records before filtering: {len(results_df)}")
        
        # Filter to include only addresses containing 'LOUISVILLE, KY'
        filtered_df = results_df[results_df['Address'].str.contains('LOUISVILLE, KY', na=False)]
        
        logging.info(f"Successfully filtered for Louisville results. Remaining records: {len(filtered_df)}")
        return filtered_df
    except Exception as e:
        logging.error(f"Error filtering results for Louisville addresses: {e}")
        raise

# Step 2: Load ArcGIS data for fuzzy matching
def load_arcgis_data():
    url = 'https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/tobacco_licenses/FeatureServer/0/query'
    params = {
        'where': '1=1',
        'outFields': 'Business_Name,Address,Latitude,Longitude',
        'outSR': '4326',
        'f': 'json'
    }

    try:
        logging.info("Start loading ArcGIS data")
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()

        arcgis_results = [
            {
                'Business_Name': feature['attributes'].get('Business_Name', 'No Name'),
                'Address': feature['attributes']['Address'].strip().upper(),  # Capitalized for matching
                'Latitude': feature['attributes']['Latitude'],
                'Longitude': feature['attributes']['Longitude']
            }
            for feature in data['features']
        ]

        arcgis_df = pd.DataFrame(arcgis_results)
        logging.info(f"Successfully loaded {len(arcgis_df)} entries from ArcGIS data")
        return arcgis_df

    except Exception as e:
        logging.error(f"Failed to fetch ArcGIS data: {e}")
        raise

# Step 3: Fuzzy matching process
def perform_fuzzy_matching(google_df, arcgis_df):
    matched_results = []
    unmatched_google_addresses = []  # Initialize a list to store unmatched addresses
    
    try:
        logging.info("Start performing fuzzy matching")
        for idx, google_row in google_df.iterrows():
            google_address = preprocess_address(google_row['Address'])  # Preprocess Google address
            
            # Find the best match using fuzzy matching
            best_match = process.extractOne(google_address, arcgis_df['Address'], scorer=fuzz.token_sort_ratio)
            
            if best_match[1] >= 60:  # You can set a threshold for a match score
                matched_results.append({
                    'Google Place Name': google_row['Place Name'],
                    'Google Address': google_row['Address'],  # Original Google Address for reference
                    'ArcGIS Best Match': best_match[0],
                    'Match Score': best_match[1],
                    'Matched Street Name': best_match[0]  # Get the street name from ArcGIS
                })
            else:
                # If no match, still append the closest match
                unmatched_google_addresses.append({
                    'Google Place Name': google_row['Place Name'],
                    'Google Address': google_row['Address'],  # Original Google Address for reference
                    'Closest ArcGIS Match': best_match[0],
                    'Closest Match Score': best_match[1]
                })  # Store unmatched row with closest match info

        matched_df = pd.DataFrame(matched_results)
        unmatched_df = pd.DataFrame(unmatched_google_addresses)  # Create a DataFrame for unmatched addresses
        
        logging.info(f"Successfully performed fuzzy matching. Matched: {len(matched_df)}, Unmatched: {len(unmatched_df)}")
        return matched_df, unmatched_df

    except Exception as e:
        logging.error(f"Error during fuzzy matching: {e}")
        raise

# Function to save results to CSV
def save_results_to_csv(matched_df, unmatched_df):
    try:
        matched_file_path = f'matched_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        unmatched_file_path = f'unmatched_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        matched_df.to_csv(matched_file_path, index=False)
        unmatched_df.to_csv(unmatched_file_path, index=False)
        
        logging.info(f"Matched results saved to {matched_file_path}")
        logging.info(f"Unmatched results saved to {unmatched_file_path}")
    except Exception as e:
        logging.error(f"Failed to save results to CSV: {e}")
        raise

def main():
    try:
        # Step 1: Load configurations
        api_key, queries_df = load_config_from_yaml('config.yaml')
        # Step 2: Load rectangle coordinates
        coordinates_df = load_coordinates_from_csv('coordinates.csv')
        # Step 3: Get tobacco shops from Google Places API
        results_df, totals = get_tobacco_shops(api_key, coordinates_df, queries_df)
        # Step 4: Filter results for Louisville, KY
        louisville_results_df = filter_louisville_results(results_df)
        # Step 5: Load ArcGIS data for fuzzy matching
        arcgis_df = load_arcgis_data()
        # Step 6: Perform fuzzy matching
        matched_df, unmatched_df = perform_fuzzy_matching(louisville_results_df, arcgis_df)
        # Step 7: Save results to CSV files
        save_results_to_csv(matched_df, unmatched_df)
    except Exception as e:
        logging.error(f"An error occurred in main: {e}")

if __name__ == "__main__":
    main()