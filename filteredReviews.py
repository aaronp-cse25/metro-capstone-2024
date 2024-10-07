import csv
import requests

# API key (Replace with your actual API key)
credentials = 'AIzaSyA6HnFsDI6RGEH_OrR7OTJlqr2e_T0pQ9A'

# Keywords to filter reviews
keywords = ['tobacco', 'vape', 'cigarette', 'hookah', 'cannibus', 'kratom']

# Function to load place IDs from results.txt and strip spaces from headers
def load_place_ids(file_name):
    places = []
    try:
        with open(file_name, mode='r') as file:
            csv_reader = csv.DictReader(file)
            # Strip spaces from headers
            csv_reader.fieldnames = [header.strip() for header in csv_reader.fieldnames]
           # print(f"Processed Headers: {csv_reader.fieldnames}")
            for row in csv_reader:
                place_id = row['Place ID'].strip()
                name = row['Place Name'].strip()
                if place_id and name:
                    places.append({
                        'place_id': place_id,
                        'name': name
                    })
                else:
                    print(f"Warning: No 'Place ID' found for {row}")
    except Exception as e:
        print(f"Error reading {file_name}: {e}")
    return places

# Function to fetch reviews using place_id
def fetch_reviews(place_id):
    details_url = f"https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        'place_id': place_id,
        'fields': 'reviews',
        'key': credentials
    }
    try:
        response = requests.get(details_url, params=params)
        response.raise_for_status()  # Raise an error for bad status codes
        details_response = response.json()

        # Extract the reviews if present
        reviews = details_response.get('result', {}).get('reviews', [])
        return reviews
    except requests.exceptions.RequestException as e:
        print(f"Error fetching details for place_id {place_id}: {e}")
        return []

# Function to filter reviews by keywords
def filter_reviews(reviews, keywords):
    filtered_reviews = []
    for review in reviews:
        text = review.get('text', '').lower()
        if any(keyword.lower() in text for keyword in keywords):
            filtered_reviews.append(review)
    return filtered_reviews

# Function to fetch and filter reviews, and store places into two lists
def fetch_and_store_reviews(file_name):
    # Load place IDs from results file
    places = load_place_ids(file_name)

    # Lists to store places based on review matches
    places_with_matching_reviews = []
    places_without_matching_reviews = []

    # Fetch and filter reviews for each place
    for place in places:
        place_id = place['place_id']
        name = place['name']
        reviews = fetch_reviews(place_id)
        filtered_reviews = filter_reviews(reviews, keywords)

        if filtered_reviews:
            places_with_matching_reviews.append({
                'name': name,
                'place_id': place_id,
                'filtered_reviews': filtered_reviews
            })
        else:
            places_without_matching_reviews.append({
                'name': name,
                'place_id': place_id
            })

    # Print results: places with and without matching reviews
    print("\nPlaces with matching keyword reviews:")
    for place in places_with_matching_reviews:
        print(f"Name: {place['name']}, Place ID: {place['place_id']}")
        # Uncomment below to print filtered reviews
        # for review in place['filtered_reviews']:
        #     print(f" - {review['text']} (Rating: {review['rating']})")

    print("\nPlaces without matching keyword reviews:")
    for place in places_without_matching_reviews:
        print(f"Name: {place['name']}, Place ID: {place['place_id']}")

    # Optional: Store the places into files or do further processing if needed

# Example call to fetch, filter, and print the places
fetch_and_store_reviews('results.txt')
