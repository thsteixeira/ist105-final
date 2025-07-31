from django.shortcuts import render, redirect
from django.contrib import messages
import requests
import logging
import json

from .forms import TravelHistoryForm
from .models import TravelHistory
from .get_locations import get_locations_from_api
from .get_weather import get_weather
from .get_directions import get_directions_between_locations

# Create your views here.

def parse_stored_data(data_string):
    """
    Parse stored JSON string data safely
    """
    if isinstance(data_string, dict):
        return data_string
    
    if data_string is None or data_string == '':
        return {}
    
    if isinstance(data_string, str):
        try:
            # Try to parse as JSON first
            if data_string.startswith('{') or data_string.startswith('['):
                # Clean up the string for JSON parsing
                clean_string = data_string.replace("'", '"').replace('True', 'true').replace('False', 'false')
                return json.loads(clean_string)
            else:
                # If it's not JSON, try to evaluate it safely (for dict strings)
                import ast
                return ast.literal_eval(data_string)
        except (json.JSONDecodeError, ValueError, SyntaxError) as e:
            # If parsing fails, return error dict
            return {'error': f'Data parsing failed: {str(e)}'}
    
    return data_string

def format_weather_for_history(weather_data):
    """
    Format weather data for history display
    """
    if isinstance(weather_data, str):
        weather_data = parse_stored_data(weather_data)
    
    # Check if parsing failed
    if isinstance(weather_data, dict) and 'error' in weather_data and 'Data parsing failed' in weather_data.get('error', ''):
        return "Weather data corrupted"
    
    if isinstance(weather_data, dict):
        if 'error' in weather_data:
            return "Weather Error"
        
        name = weather_data.get('name', 'Unknown')
        temp = weather_data.get('main', {}).get('temp', 'N/A')
        description = weather_data.get('weather', [{}])[0].get('description', 'N/A')
        
        return f"{name}: {temp}°C, {description.title()}"
    
    return "Weather unavailable"

def format_directions_for_history(directions_data):
    """
    Format directions data for history display
    """
    if isinstance(directions_data, str):
        directions_data = parse_stored_data(directions_data)
    
    # Check if parsing failed
    if isinstance(directions_data, dict) and 'error' in directions_data and 'Data parsing failed' in directions_data['error']:
        return "Directions data corrupted"
    
    if isinstance(directions_data, dict):
        if not directions_data.get('success', False):
            return directions_data.get('error', 'Unknown error')
        
        duration_minutes = int(directions_data.get('duration', 0)) // 60
        distance_km = directions_data.get('distance', 0) / 1000
        
        return f"{duration_minutes} min, {distance_km:.1f} km"
    
    return "Directions unavailable"


def format_weather_data(weather_data):
    """
    Format weather data for display in templates
    """
    if isinstance(weather_data, dict):
        if 'error' in weather_data:
            return f"Weather Error: {weather_data['error']}"
        
        # Extract useful weather information
        try:
            name = weather_data.get('name', 'Unknown Location')
            temp = weather_data.get('main', {}).get('temp', 'N/A')
            description = weather_data.get('weather', [{}])[0].get('description', 'N/A')
            humidity = weather_data.get('main', {}).get('humidity', 'N/A')
            
            return f"{name}: {temp}°C, {description.title()}, Humidity: {humidity}%"
        except (KeyError, IndexError, TypeError):
            return "Weather data unavailable"
    
    return str(weather_data)

def format_directions_data(directions_data):
    """
    Format directions data for display in templates
    """
    if isinstance(directions_data, dict):
        if not directions_data.get('success', False):
            return f"Directions Error: {directions_data.get('error', 'Unknown error')}"
        
        try:
            duration_minutes = directions_data['duration'] // 60
            distance_km = directions_data['distance'] / 1000
            
            result = f"Route: {duration_minutes} minutes, {distance_km:.1f} km\n\n"
            
            # Add all direction steps
            steps = directions_data.get('steps', [])
            if steps:
                result += "Turn-by-turn Directions:\n"
                result += "-" * 40 + "\n"
                for i, step in enumerate(steps, 1):
                    instruction = step.get('instruction', 'N/A')
                    step_distance_km = step.get('distance', 0) / 1000
                    result += f"{i}. {instruction} ({step_distance_km:.1f} km)\n"
            else:
                result += "No detailed directions available."
            
            return result
        except (KeyError, TypeError, ZeroDivisionError):
            return "Directions data unavailable"
    
    return str(directions_data)

def travel_form_view(request):
    """
    View to handle the travel form with API-fetched locations
    """
    # Get locations from API
    location_choices = get_locations_from_api()
    
    if request.method == 'POST':
        form = TravelHistoryForm(request.POST, location_choices=location_choices)
        if form.is_valid():
            start_city = form.cleaned_data['start']
            destination_city = form.cleaned_data['destination']
            
            # Get weather data
            start_weather = get_weather(start_city)
            destination_weather = get_weather(destination_city)
            
            # Get directions
            directions = get_directions_between_locations(start_city, destination_city)
            
            # Format data for display
            messages = {
                'start': start_city,
                'destination': destination_city,
                'start_weather': format_weather_data(start_weather),
                'destination_weather': format_weather_data(destination_weather),
                'directions': format_directions_data(directions)
            }
            
            # Save to database
            travel_history = form.save(commit=False)
            travel_history.start_weather = str(start_weather)
            travel_history.destination_weather = str(destination_weather)
            travel_history.directions = str(directions)
            travel_history.save()
            
            # Redirect after successful submission
            return render(request, 'smartravelapp/result.html', {
                'messages': messages
            })
    else:
        form = TravelHistoryForm(location_choices=location_choices)
    
    return render(request, 'smartravelapp/travel_form.html', {
        'form': form,
        'title': 'Smart Travel Form'
    })

def travel_history_list(request):
    """
    View to display list of travel histories with formatted data
    """
    histories = TravelHistory.objects.all().order_by('-time')
    
    # Format the data for better display
    formatted_histories = []
    for history in histories:
        formatted_history = {
            'id': history.id,
            'start': history.start,
            'destination': history.destination,
            'time': history.time,
            'start_weather': format_weather_for_history(history.start_weather),
            'destination_weather': format_weather_for_history(history.destination_weather),
            'directions': format_directions_for_history(history.directions)
        }
        formatted_histories.append(formatted_history)
    
    return render(request, 'smartravelapp/travel_history.html', {
        'histories': formatted_histories,
        'title': 'Travel History'
    })
