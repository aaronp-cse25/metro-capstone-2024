import os
import pandas as pd
import requests
from pyproj import Transformer

# Get the current directory of the script
current_folder = os.getcwd()

# Construct output file path relative to the current directory
output_file = os.path.join(current_folder, 'coordinates.csv')

# Function to load data from ArcGIS Feature Server
def load_arcgis_data():
    url = 'https://services1.arcgis.com/79kfd2K6fskCAkyg/ArcGIS/rest/services/Jefferson_County_Grid/FeatureServer/0/query'
    params = {
        'where': '1=1',  # Fetch all records
        'outFields': '*',  # Select all fields
        'f': 'json'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        
        # Extract relevant features
        features = data['features']
        records = []
        
        for feature in features:
            attributes = feature['attributes']
            records.append({
                'XMIN': attributes['XMIN'],  # Replace with your actual field names
                'YMIN': attributes['YMIN'],
                'XMAX': attributes['XMAX'],
                'YMAX': attributes['YMAX']
            })
        
        df = pd.DataFrame(records)
        return df
    
    except Exception as e:
        print(f"Failed to load ArcGIS data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on failure

# Load the data from ArcGIS
df = load_arcgis_data()

# Check if DataFrame is empty
if df.empty:
    print("No data available for transformation.")
else:
    # Create a Transformer object from EPSG:2246 to EPSG:4326 (WGS84)
    transformer = Transformer.from_crs("EPSG:2246", "EPSG:4326")

    # Define a function to transform the coordinates and return in the correct order
    def transform_coordinates(row):
        low_lat, low_lon = transformer.transform(row['XMIN'], row['YMIN'])  # Lower bound (lat, lon)
        high_lat, high_lon = transformer.transform(row['XMAX'], row['YMAX'])  # Upper bound (lat, lon)
        return pd.Series([low_lat, low_lon, high_lat, high_lon], index=['Low_Lat', 'Low_Lon', 'High_Lat', 'High_Lon'])

    # Apply the transformation to each row
    transformed_df = df.apply(transform_coordinates, axis=1)

    # Save the transformed coordinates to a new CSV file
    transformed_df.to_csv(output_file, index=False)

    print(f"Transformed CSV saved to {output_file}")
