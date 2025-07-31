import requests
import json
import logging

class DirectionsAPI:
    """
    Fetches driving directions between two locations using OpenRouteService API.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the DirectionsAPI with API key and endpoints.
        """
        # Use provided API key or default to your actual key
        self.api_key = api_key or "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjBhY2Q2MWUyMzE4MTRmYzA5M2EwMGI3ZDkwNmJiNzE1IiwiaCI6Im11cm11cjY0In0="
        self.directions_api = "https://api.openrouteservice.org/v2/directions/driving-car"
        self.geocode_api = "https://api.openrouteservice.org/geocode/search"
        
    def geocode_address(self, address):
        """
        Geocode an address to get its coordinates using only the API.
        
        Args:
            address (str): The address to geocode
            
        Returns:
            list: [longitude, latitude] coordinates or None if failed
        """
        # Try multiple search strategies to improve geocoding accuracy
        search_queries = [
            f"{address}, British Columbia, Canada",  # Most specific
            f"{address}, BC, Canada",                # Medium specific
            f"{address}, Canada",                    # Less specific
            address                                  # Least specific
        ]
        
        for search_query in search_queries:
            print(f"Trying to geocode: '{search_query}'")
            
            url = f"{self.geocode_api}?api_key={self.api_key}&text={search_query}&boundary.country=CA&size=1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                json_data = response.json()
                if json_data.get("features"):
                    coords = json_data["features"][0]["geometry"]["coordinates"]
                    
                    # Validate coordinates (longitude, latitude)
                    if -180 <= coords[0] <= 180 and -90 <= coords[1] <= 90:
                        print(f"Successfully geocoded '{address}' to coordinates: {coords}")
                        return coords
                    else:
                        print(f"Invalid coordinates received for '{address}': {coords}")
                        continue
                else:
                    print(f"No results found for query: '{search_query}'")
                    continue
            else:
                print(f"Geocoding API error for '{search_query}': {response.status_code} - {response.text}")
                continue
        
        # If all search strategies failed
        print(f"Failed to geocode address '{address}' with all search strategies")
        return None
    
    def get_directions(self, origin, destination):
        """
        Get driving directions between two locations using only API geocoding.
        
        Args:
            origin (str): Starting location/address
            destination (str): Destination location/address
            
        Returns:
            dict: Direction data with route info, duration, distance, and steps
        """
        print(f"Getting directions from '{origin}' to '{destination}'")
        
        # Geocode the addresses using API only
        orig_coords = self.geocode_address(origin)
        dest_coords = self.geocode_address(destination)

        if not orig_coords:
            return {
                'success': False,
                'error': f"Unable to geocode origin address: '{origin}'. Please check the spelling or try a more specific location name."
            }
        
        if not dest_coords:
            return {
                'success': False,
                'error': f"Unable to geocode destination address: '{destination}'. Please check the spelling or try a more specific location name."
            }

        print(f"Attempting to route from {orig_coords} to {dest_coords}")

        # Construct the JSON body for the POST request
        body = {
            "coordinates": [orig_coords, dest_coords]
        }

        # Make the POST request
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        
        response = requests.post(self.directions_api, headers=headers, json=body, timeout=15)
        
        if response.status_code == 200:
            json_data = response.json()
            if 'routes' in json_data and json_data['routes']:
                route = json_data['routes'][0]
                if 'segments' in route and route['segments']:
                    segment = route['segments'][0]
                    
                    # Extract trip duration and distance
                    duration = segment.get('duration', 0)
                    distance = segment.get('distance', 0)
                    
                    # Extract step-by-step directions
                    steps = []
                    if 'steps' in segment:
                        for step in segment['steps']:
                            instruction = step.get('instruction', 'N/A')
                            step_distance = step.get('distance', 0)
                            steps.append({
                                'instruction': instruction,
                                'distance': step_distance
                            })
                    
                    return {
                        'success': True,
                        'origin': origin,
                        'destination': destination,
                        'duration': duration,  # in seconds
                        'distance': distance,  # in meters
                        'steps': steps,
                        'raw_data': json_data
                    }
                else:
                    return {
                        'success': False,
                        'error': "No segments found in the route."
                    }
            else:
                return {
                    'success': False,
                    'error': "No routes found in the response."
                }
        else:
            # Handle specific API errors
            error_data = response.json()
            if 'error' in error_data:
                error_message = error_data['error'].get('message', 'Unknown API error')
                if 'routable point' in error_message:
                    return {
                        'success': False,
                        'error': f"Routing failed: Cannot find drivable roads near the geocoded location for {origin} or {destination}. The API coordinates may point to an area without vehicle access (like a park, water body, or pedestrian area). You might try using a more specific address or nearby landmark."
                    }
                elif 'coordinate' in error_message:
                    return {
                        'success': False,
                        'error': f"Coordinate error: The geocoded coordinates for {origin} or {destination} are not suitable for vehicle routing. This location might be in a restricted area or the geocoding result needs refinement."
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Routing error: {error_message}"
                    }
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code} - {response.text[:200]}"
                }
    
    def format_directions_summary(self, directions_data):
        """
        Format directions data into a readable summary string.
        
        Args:
            directions_data (dict): The result from get_directions()
            
        Returns:
            str: Formatted summary of the route
        """
        if not directions_data.get('success'):
            return f"Error: {directions_data.get('error', 'Unknown error')}"
        
        duration_minutes = directions_data['duration'] // 60
        distance_km = directions_data['distance'] / 1000
        
        summary = f"Route from {directions_data['origin']} to {directions_data['destination']}\n"
        summary += f"Duration: {duration_minutes} minutes\n"
        summary += f"Distance: {distance_km:.2f} km\n"
        summary += "Directions:\n"
        
        for i, step in enumerate(directions_data['steps'], 1):
            step_distance_km = step['distance'] / 1000
            summary += f"{i}. {step['instruction']} ({step_distance_km:.2f} km)\n"
        
        return summary
    
    def print_directions(self, origin, destination):
        """
        Get and print formatted directions between two locations.
        
        Args:
            origin (str): Starting location/address
            destination (str): Destination location/address
        """
        print(f"\nGetting directions from {origin} to {destination}...")
        print("=" * 50)
        
        directions = self.get_directions(origin, destination)
        
        if directions['success']:
            print("API Status: Successful route call.\n")
            print("=" * 50)
            print(f"Directions from {origin} to {destination}")
            
            duration_minutes = directions['duration'] // 60
            distance_km = directions['distance'] / 1000
            
            print(f"Trip Duration: {duration_minutes} minutes ({directions['duration']} seconds)")
            print(f"Distance: {distance_km:.2f} km ({directions['distance']} meters)")
            print("=" * 50)
            
            for i, step in enumerate(directions['steps'], 1):
                step_distance_km = step['distance'] / 1000
                print(f"{i}. {step['instruction']} ({step_distance_km:.2f} km)")
            
            print("=" * 50)
        else:
            print(f"Error: {directions['error']}")
        print()


# Function for easy import in Django views
def get_directions_between_locations(origin, destination, api_key=None):
    """
    Convenience function to get directions between two locations.
    
    Args:
        origin (str): Starting location
        destination (str): Destination location
        api_key (str): OpenRouteService API key (optional, uses default if not provided)
        
    Returns:
        dict: Direction data or error information
    """
    directions_api = DirectionsAPI(api_key)
    return directions_api.get_directions(origin, destination)


# Example usage
if __name__ == "__main__":
    # Example usage of the DirectionsAPI class
    api = DirectionsAPI()  # Uses the default API key
    
    # Test with sample locations
    origin = "Vancouver, BC"
    destination = "Victoria, BC"
    
    # Method 1: Get structured data
    directions = api.get_directions(origin, destination)
    if directions['success']:
        print("Route found successfully!")
        summary = api.format_directions_summary(directions)
        print(summary)
    else:
        print(f"Error: {directions['error']}")
    
    # Method 2: Print formatted directions
    api.print_directions(origin, destination)
