#!/usr/bin/env python
"""
Waybar weather module script that fetches weather data from OpenWeatherMap
Displays current weather with emoji and temperature in the bar
Shows detailed forecast in the tooltip
"""

import json
import requests
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path

# Dictionary mapping OpenWeatherMap codes to emoji representations
WEATHER_CODES = {
    # Thunderstorm
    "200": "⛈️",  # thunderstorm with light rain
    "201": "⛈️",  # thunderstorm with rain
    "202": "⛈️",  # thunderstorm with heavy rain
    "210": "🌩️",  # light thunderstorm
    "211": "🌩️",  # thunderstorm
    "212": "🌩️",  # heavy thunderstorm
    "221": "🌩️",  # ragged thunderstorm
    "230": "⛈️",  # thunderstorm with light drizzle
    "231": "⛈️",  # thunderstorm with drizzle
    "232": "⛈️",  # thunderstorm with heavy drizzle
    
    # Drizzle
    "300": "🌧️",  # light intensity drizzle
    "301": "🌧️",  # drizzle
    "302": "🌧️",  # heavy intensity drizzle
    "310": "🌧️",  # light intensity drizzle rain
    "311": "🌧️",  # drizzle rain
    "312": "🌧️",  # heavy intensity drizzle rain
    "313": "🌧️",  # shower rain and drizzle
    "314": "🌧️",  # heavy shower rain and drizzle
    "321": "🌧️",  # shower drizzle
    
    # Rain
    "500": "🌧️",  # light rain
    "501": "🌧️",  # moderate rain
    "502": "🌧️",  # heavy intensity rain
    "503": "🌧️",  # very heavy rain
    "504": "🌧️",  # extreme rain
    "511": "🌨️",  # freezing rain
    "520": "🌧️",  # light intensity shower rain
    "521": "🌧️",  # shower rain
    "522": "🌧️",  # heavy intensity shower rain
    "531": "🌧️",  # ragged shower rain
    
    # Snow
    "600": "🌨️",  # light snow
    "601": "🌨️",  # snow
    "602": "🌨️",  # heavy snow
    "611": "🌨️",  # sleet
    "612": "🌨️",  # light shower sleet
    "613": "🌨️",  # shower sleet
    "615": "🌨️",  # light rain and snow
    "616": "🌨️",  # rain and snow
    "620": "🌨️",  # light shower snow
    "621": "🌨️",  # shower snow
    "622": "🌨️",  # heavy shower snow
    
    # Atmosphere
    "701": "🌫️",  # mist
    "711": "🌫️",  # smoke
    "721": "🌫️",  # haze
    "731": "🌫️",  # sand/dust whirls
    "741": "🌫️",  # fog
    "751": "🌫️",  # sand
    "761": "🌫️",  # dust
    "762": "🌫️",  # volcanic ash
    "771": "💨",  # squalls
    "781": "🌪️",  # tornado
    
    # Clear and Clouds
    "800": "☀️",   # clear sky
    "801": "⛅",  # few clouds: 11-25%
    "802": "☁️",   # scattered clouds: 25-50%
    "803": "☁️",   # broken clouds: 51-84%
    "804": "☁️"    # overcast clouds: 85-100%
}

# Cache settings
CACHE_DIR = Path(os.path.expanduser("~/.cache/waybar-weather"))
CACHE_FILE = CACHE_DIR / "weather_cache.pkl"
CACHE_DURATION = 3600  # 1 hour in seconds

# Create cache directory if it doesn't exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize data dictionary for waybar output
data = {}

def load_cached_data():
    """Load cached weather data if it exists and is fresh"""
    try:
        if CACHE_FILE.exists():
            cache_age = datetime.now().timestamp() - CACHE_FILE.stat().st_mtime
            if cache_age < CACHE_DURATION:
                with open(CACHE_FILE, 'rb') as f:
                    return pickle.load(f)
    except Exception:
        pass
    return None

def save_cached_data(weather_data, location_data):
    """Save weather and location data to cache"""
    try:
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump((weather_data, location_data), f)
    except Exception:
        pass

# Read config file for API key
config_file = os.path.expanduser('~/.config/HyprV/hyprv.conf')
api_key = None

try:
    with open(config_file, 'r') as f:
        for line in f:
            if line.startswith('OPENWEATHERMAP_API_KEY='):
                api_key = line.split('=')[1].strip().strip('"')
    
    if not api_key:
        print(json.dumps({"text": "❌", "tooltip": "API key not set in hyprv.conf"}))
        exit(0)
except FileNotFoundError:
    print(json.dumps({"text": "❌", "tooltip": "hyprv.conf not found"}))
    exit(0)

try:
    # Check cache first
    cached_data = load_cached_data()
    if cached_data:
        weather, location = cached_data
    else:
        # Fetch current weather and forecast from OpenWeatherMap
        # Get location from IP
        ip_response = requests.get("https://ipapi.co/json/")
        ip_response.raise_for_status()
        location = ip_response.json()
        
        lat = location['latitude']
        lon = location['longitude']
        
        # Get current weather and forecast
        weather_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely&units=metric&appid={api_key}"
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()
        weather = weather_response.json()
        
        # Save to cache
        save_cached_data(weather, location)

except requests.RequestException as e:
    print(json.dumps({"text": "❌", "tooltip": f"Weather API error: {str(e)}"}))
    exit(0)
except (KeyError, IndexError) as e:
    print(json.dumps({"text": "❌", "tooltip": f"Data parsing error: {str(e)}"}))
    exit(0)


def format_time(timestamp):
    """Format timestamp to hour:minute"""
    return datetime.fromtimestamp(timestamp).strftime("%H:%M")

def format_temp(temp):
    """Format temperature with degree symbol"""
    return f"{temp:.1f}°"

def format_chances(hour_data):
    """Format weather probabilities from OpenWeatherMap data"""
    conditions = []
    
    if 'pop' in hour_data and hour_data['pop'] > 0:
        conditions.append(f"Rain {int(hour_data['pop'] * 100)}%")
    
    if 'clouds' in hour_data and hour_data['clouds'] > 50:
        conditions.append(f"Clouds {hour_data['clouds']}%")
        
    return ", ".join(conditions)

def get_weather_emoji(weather_id):
    """Get weather emoji based on OpenWeatherMap condition code"""
    code_str = str(weather_id)
    
    # First try exact match
    if code_str in WEATHER_CODES:
        return WEATHER_CODES[code_str]
    
    # Then try category match (first digit)
    return WEATHER_CODES.get(code_str[0], "❓")

def get_aqi(lat, lon):
    """Fetch AQI data using OpenWeatherMap API"""
    try:
        with open(config_file, 'r') as f:
            for line in f:
                if line.startswith('OPENWEATHERMAP_API_KEY='):
                    api_key = line.split('=')[1].strip().strip('"')
                    break
        if not api_key:
            return "N/A"
        
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
        response = requests.get(url)
        data = response.json()
        aqi = data['list'][0]['main']['aqi']
        aqi_labels = {
            1: "Good",
            2: "Fair",
            3: "Moderate",
            4: "Poor",
            5: "Very Poor"
        }
        return f"{aqi}/5 ({aqi_labels[aqi]})"
    except:
        return "N/A"


# Prepare the main display text for waybar
current = weather['current']
temp = current['temp']
feels_like = current['feels_like']
weather_id = current['weather'][0]['id']

# Handle special formatting for positive single-digit temperatures
tempint = int(weather['current']['feels_like'])
extrachar = ''
if tempint > 0 and tempint < 10:
    extrachar = '+'  # Add plus sign for positive single digits

data['text'] = get_weather_emoji(weather['current']['weather'][0]['id']) + \
    " " + extrachar + f"{feels_like:.0f}°"

# Build detailed tooltip with current conditions and forecast
aqi = get_aqi(lat, lon)

data['tooltip'] = f"<b>{location['city']}, {location['country_name']}</b>\n"
data['tooltip'] += f"<b>{current['weather'][0]['description'].capitalize()} {temp:.1f}°</b>\n"
data['tooltip'] += f"Feels like: {feels_like:.1f}°\n"
data['tooltip'] += f"Wind: {current['wind_speed']:.1f} m/s\n"
data['tooltip'] += f"Humidity: {current['humidity']}%\n"
data['tooltip'] += f"AQI: {aqi}\n"


# Daily forecast with hourly details
for i, day in enumerate(weather['daily'][:2]):  # Only today and tomorrow
    data['tooltip'] += "\n<b>"
    forecast_date = datetime.fromtimestamp(day['dt'])
    if i == 0:
        data['tooltip'] += "Today, "
    elif i == 1:
        data['tooltip'] += "Tomorrow, "
    data['tooltip'] += f"{forecast_date.strftime('%Y-%m-%d')}</b>\n"
    
    data['tooltip'] += f"⬆️ {day['temp']['max']:.1f}° ⬇️ {day['temp']['min']:.1f}° "
    data['tooltip'] += f"🌅 {datetime.fromtimestamp(day['sunrise']).strftime('%H:%M')} "
    data['tooltip'] += f"🌇 {datetime.fromtimestamp(day['sunset']).strftime('%H:%M')}\n"

    # Get hourly data for this day
    day_start = forecast_date.replace(hour=0, minute=0, second=0).timestamp()
    day_end = forecast_date.replace(hour=23, minute=59, second=59).timestamp()
    
    # Show forecasts every 3 hours
    for hour in weather['hourly']:
        hour_time = datetime.fromtimestamp(hour['dt'])
        
        # Only show hours for this day
        if day_start <= hour['dt'] <= day_end:
            # For today, skip past hours
            if i == 0 and hour_time.hour < datetime.now().hour - 2:
                continue
                
            # Only show forecasts every 3 hours
            if hour_time.hour % 3 == 0:
                weather_emoji = get_weather_emoji(hour['weather'][0]['id'])
                data['tooltip'] += (
                    f"{hour_time.strftime('%H:%M')} {weather_emoji} "
                    f"{format_temp(hour['temp'])} "
                    f"{hour['weather'][0]['description'].capitalize()}, "
                    f"{format_chances(hour)}\n"
                )


print(json.dumps(data))
