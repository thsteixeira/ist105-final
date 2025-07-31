import requests
import logging

logging.basicConfig(level=logging.INFO)

class LocationAPI:
    """
    Fetches locations from an external API and returns them as a list of tuples.
    """
    
    @staticmethod
    def get_locations_from_api():
        """
        Fetch locations from the GeoDB API for British Columbia cities
        """
        try:
            # Request more cities by adding limit parameter
            response = requests.get(
                'http://geodb-free-service.wirefreethought.com/v1/geo/countries/CA/regions/BC/cities?limit=50&minPopulation=1000',
                timeout=10
            )
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()
            
            # The API returns data in format: {"data": [{"id": 1, "name": "City"}], ...}
            locations = []
            if 'data' in data:
                for loc in data['data']:
                    # Use city name as both value and display text
                    location_name = loc.get('name', 'Unknown')
                    # Only add if we have a valid name
                    if location_name and location_name != 'Unknown':
                        locations.append((location_name, location_name))
            
            # Limit to first 20 cities after the empty choice
            limited_locations = locations[:20]
            
            # Add default empty choice at the beginning
            return [('', 'Select a location')] + limited_locations
        
        except requests.RequestException as e:
            logging.error(f"Error fetching locations: {e}")
            # Return expanded fallback locations on error (20 major Canadian cities)
            return [
                ('', 'Select a location'),
                ('Vancouver', 'Vancouver'),
                ('Victoria', 'Victoria'),
                ('Burnaby', 'Burnaby'),
                ('Richmond', 'Richmond'),
                ('Surrey', 'Surrey'),
                ('Abbotsford', 'Abbotsford'),
                ('Coquitlam', 'Coquitlam'),
                ('Langley', 'Langley'),
                ('Saanich', 'Saanich'),
                ('Delta', 'Delta'),
                ('North Vancouver', 'North Vancouver'),
                ('Maple Ridge', 'Maple Ridge'),
                ('Nanaimo', 'Nanaimo'),
                ('New Westminster', 'New Westminster'),
                ('West Vancouver', 'West Vancouver'),
                ('Port Coquitlam', 'Port Coquitlam'),
                ('White Rock', 'White Rock'),
                ('Prince George', 'Prince George'),
                ('Chilliwack', 'Chilliwack'),
                ('Kamloops', 'Kamloops'),
            ]
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return [('', 'Select a location')]

def get_locations_from_api():
    """
    Function wrapper for easier importing in views
    """
    return LocationAPI.get_locations_from_api()

if __name__ == "__main__":
    # Example usage
    locations = get_locations_from_api()
    print("Fetched locations:")
    for loc_id, loc_name in locations:
        print(f"  {loc_id}: {loc_name}")
    print(f"\nTotal locations: {len(locations)}")