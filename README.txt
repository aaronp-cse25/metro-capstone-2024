# metro-capstone-2024
CSE Capstone Fall 2024. Group 4 project working with Louisville Metro.

Brief How-to guide:
run_scripts.py will run places.py and filteredReviews.py in order
places.py queries 100 sum boxes for queries from the yaml config over Louisville
places.py produces logs.txt with numerical outputs
places.py finds 1500 results, 1300 in Louisville, matches 1200 to the License database found in matched_results, 
and leaves 111 results in unmatched_results for further examination

filteredReviews.py loads unmatched_results, and queries all place IDs for each keyword from the yaml config
filteredReviews.py does not find positive reviews for 106 places, and places them in unmatched_2.csv
filteredReviews.py finds positive reviews for 5 places, and puts them in matched_2.csv

both files read and config from config.yaml
The above testing was completed with the following queries and keywords:

queries:
  - tobacco
  - gas station
  - convenience store
  - liquor store
  - pharmacy

keywords:
  - marlboro
  - camel
  - newport
  - vape
  - smoke
  - cigarette
  - fog
  - cigar
  - cloud
  - tobacco
  - smoke
  - snuff
  - loose leaf
  - chewing tobacco
  - vape
  - vapor
  - smoke shop
  - smoker
  - cigs

