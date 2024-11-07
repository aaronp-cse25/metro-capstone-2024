import csv
import requests
import yaml
import pandas as pd
import logging
import os

# Function to load config from YAML
def load_config_from_yaml(file_path):
    try:
        with open(file_path, 'r') as file:
            config_data = yaml.safe_load(file)
        keywords_df = pd.DataFrame(config_data['keywords'], columns=['keyword'])
        credentials = config_data['api_key']
        logging.info("Loaded config from YAML successfully")
        return credentials, keywords_df
    except Exception as e:
        logging.error(f"Failed to load config from YAML: {e}")
        raise

# Function to load place IDs, Names, and Addresses from CSV
def load_place_ids(file_name):
    try:
        df = pd.read_csv(file_name, usecols=['Google Place ID', 'Google Place Name', 'Google Address', 'lat', 'long', 'Closest ArcGIS Match', 'Closest Match Score', 'Keywords'])
        return df
    except Exception as e:
        logging.error(f"Error reading {file_name}: {e}")
        raise

# Function to fetch reviews using place_id
def fetch_reviews(place_id, credentials):
    details_url = f"https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        'place_id': place_id,
        'fields': 'reviews',
        'key': credentials
    }
    try:
        response = requests.get(details_url, params=params)
        response.raise_for_status()
        details_response = response.json()
        reviews = details_response.get('result', {}).get('reviews', [])
        return reviews
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching details for place_id {place_id}: {e}")
        return []

# Function to filter reviews by keywords
def filter_reviews(reviews, keywords):
    filtered_reviews = []
    for review in reviews:
        text = review.get('text', '').lower()
        if any(keyword.lower() in text for keyword in keywords):
            filtered_reviews.append(review)
    return filtered_reviews

# Main function to fetch and process reviews
def fetch_and_store_reviews(file_name, credentials, keywords):
    df = load_place_ids(file_name)
    places_with_matching_reviews = []
    places_without_matching_reviews = []

    for index, row in df.iterrows():
        place_id = row['Google Place ID']
        name = row['Google Place Name']
        reviews = fetch_reviews(place_id, credentials)
        filtered_reviews = filter_reviews(reviews, keywords)
        place_info = {
            'Place ID': place_id,
            'Place Name': name,
            'Address': row['Google Address'],
            'Latitude': row["lat"],
            'Longitude': row["long"],
            'Closest ArcGIS Match': row['Closest ArcGIS Match'],
            'Closest Match Score': row['Closest Match Score'],
            'Keywords': row['Keywords']
        }
        if filtered_reviews:
            places_with_matching_reviews.append(place_info)
        else:
            places_without_matching_reviews.append(place_info)

    matched_df = pd.DataFrame(places_with_matching_reviews)
    unmatched_df = pd.DataFrame(places_without_matching_reviews)

    # Log results
    logging.info("\nPlaces with matching keyword reviews count: %d", len(matched_df))
    logging.info(matched_df.to_string())

    logging.info("\nPlaces without matching keyword reviews count: %d", len(unmatched_df))
    logging.info(unmatched_df.to_string())

    # Ensure the results directory exists
    os.makedirs('results', exist_ok=True)

    # Save DataFrames to CSVs
    matched_df.to_csv(os.path.join('results', 'review_hits.csv'), index=False)
    unmatched_df.to_csv(os.path.join('results', 'review_misses.csv'), index=False)

if __name__ == "__main__":
    # Set up logging to file
    logging.basicConfig(filename=os.path.join('results', 'log2.txt'), level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    credentials, keywords_df = load_config_from_yaml('config.yaml')
    keywords = keywords_df['keyword'].tolist()
    fetch_and_store_reviews('results/unmatched_candidates.csv', credentials, keywords)
