import requests
import logging

class WeatherAPI:
    """
    Fetches weather data for a given city using OpenWeatherMap API.
    """
    
    OPENWEATHERMAP_API_KEY = 'e6c8a91103d088a28391d8e14b75ccca'

    @staticmethod
    def get_weather(city_name):
        """
        Fetch weather data for a given city.
        """
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={WeatherAPI.OPENWEATHERMAP_API_KEY}&units=metric"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for HTTP errors
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching weather data: {e}")
            return {"error": str(e)}
        
def get_weather(city_name):
    """
    Function wrapper for easier importing in views
    """
    return WeatherAPI.get_weather(city_name)

if __name__ == "__main__":
    # Example usage
    weather = get_weather("Vancouver")
    print("Fetched weather data:")
    print(weather)