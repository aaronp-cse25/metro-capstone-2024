import os
import pandas as pd
from pyproj import Transformer
# TODO: Read in the Jefferson_State_Zones from open source database

# Get the current directory of the script
current_folder = os.getcwd()

# Construct input and output file paths relative to the current directory
input_file = os.path.join(current_folder, 'Jefferson_State_Zones.csv')
output_file = os.path.join(current_folder, 'coordinates.csv')

# Load the CSV file
df = pd.read_csv(input_file)

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
