#!/usr/bin/env python
"""
Waybar weather module script that fetches weather data from OpenWeatherMap
Displays current weather with emoji and temperature in the bar
Shows detailed forecast in the tooltip
"""

import json
import requests
import os
import sys
import pickle
import subprocess
import re
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

# Initialize location coordinates
lat = None
lon = None

def get_wifi_networks():
    """Get nearby WiFi networks using nmcli"""
    try:
        cmd = ["nmcli", "-t", "-f", "BSSID,SIGNAL", "dev", "wifi"]
        output = subprocess.check_output(cmd, text=True)
        
        wifi_points = []
        for line in output.strip().split('\n'):
            if ':' in line:
                bssid, signal = line.rsplit(':', 1)  # Split from right side once
                # Remove backslashes from MAC address
                clean_bssid = bssid.replace('\\:', ':')
                try:
                    signal_strength = int(signal.strip())
                    wifi_points.append({
                        "macAddress": clean_bssid,
                        "signalStrength": signal_strength
                    })
                except ValueError:
                    continue
        return wifi_points
    except (subprocess.SubprocessError, ValueError):
        return []

def get_location_from_wifi():
    """Get location using Google Geolocation API"""
    wifi_points = get_wifi_networks()
    if not wifi_points:
        return None
    
    # Read Google Maps API key
    api_key = None
    try:
        with open(config_file, 'r') as f:
            for line in f:
                if line.startswith('GOOGLE_MAPS_API_KEY='):
                    api_key = line.split('=')[1].strip().strip('"')
                    break
        if not api_key:
            return None
    except FileNotFoundError:
        return None

    try:
        payload = {
            "considerIp": "true",
            "wifiAccessPoints": wifi_points
        }
        
        response = requests.post(
            f"https://www.googleapis.com/geolocation/v1/geolocate?key={api_key}",
            json=payload,
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            'latitude': data['location']['lat'],
            'longitude': data['location']['lng'],
            'city': None,  # We'll need to reverse geocode these coordinates
            'country_name': None
        }
    except requests.RequestException as e:
        print(f"Google Geolocation API error: {str(e)}")
        return None

def get_location_info(lat, lon):
    """Get city and country information from coordinates using Google Geocoding API"""
    try:
        # Read Google Maps API key
        api_key = None
        with open(config_file, 'r') as f:
            for line in f:
                if line.startswith('GOOGLE_MAPS_API_KEY='):
                    api_key = line.split('=')[1].strip().strip('"')
                    break
        if not api_key:
            return {'city': 'Unknown', 'country_name': 'Unknown'}

        response = requests.get(
            f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={api_key}"
        )
        response.raise_for_status()
        data = response.json()
        
        if data['status'] != 'OK' or not data['results']:
            return {'city': 'Unknown', 'country_name': 'Unknown'}
            
        # Process address components
        address_components = data['results'][0]['address_components']
        city = None
        country = None
        
        for component in address_components:
            if 'locality' in component['types']:
                city = component['long_name']
            elif 'administrative_area_level_1' in component['types'] and not city:
                # Use state/province if city not found
                city = component['long_name']
            elif 'country' in component['types']:
                country = component['long_name']
                
        return {
            'city': city or 'Unknown',
            'country_name': country or 'Unknown'
        }
    except (requests.RequestException, KeyError, FileNotFoundError):
        return {'city': 'Unknown', 'country_name': 'Unknown'}

try:
    # Check cache first
    cached_data = load_cached_data()
    if cached_data:
        weather, location = cached_data
        lat = location['latitude']
        lon = location['longitude']
    else:
        # Try WiFi-based location first
        location = get_location_from_wifi()
        
        if location:
            lat = location['latitude']
            lon = location['longitude']
            # Get city and country info
            location_info = get_location_info(lat, lon)
            location['city'] = location_info['city']
            location['country_name'] = location_info['country_name']
        else:
            # Fallback to IP-based location
            try:
                ip_response = requests.get("https://ipapi.co/json/")
                ip_response.raise_for_status()
                location = ip_response.json()
                lat = location['latitude']
                lon = location['longitude']
            except requests.RequestException as e:
                if cached_data and "429" in str(e):
                    weather, location = cached_data
                    lat = location['latitude']
                    lon = location['longitude']
                else:
                    raise
        
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
    """Fetch AQI data using Google Air Quality API"""
    try:
        with open(config_file, 'r') as f:
            for line in f:
                if line.startswith('GOOGLE_MAPS_API_KEY='):
                    api_key = line.split('=')[1].strip().strip('"')
                    break
        if not api_key:
            return "N/A"
        
        url = f"https://airquality.googleapis.com/v1/currentConditions:lookup?key={api_key}"
        payload = {
            "location": {
                "latitude": lat,
                "longitude": lon
            },
            "extraComputations": [
                "DOMINANT_POLLUTANT_CONCENTRATION",
                "POLLUTANT_CONCENTRATION",
                "LOCAL_AQI"
            ],
            "languageCode": "en"
        }
        
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        data = response.json()
        
        # Get both AQI indexes
        uaqi_info = None
        local_info = None
        
        for index in data['indexes']:
            if index['code'] == 'uaqi':
                uaqi_info = index
            elif index['code'] == 'ind_cpcb':
                local_info = index
        
        if not local_info:
            return "N/A"  # No NAQI found
            
        # Format AQI information
        result = []
        
        # Add Local AQI Info
        result.append(f"AQI: {local_info['aqi']} ({local_info['category']})")
        
        # Add UAQI if available
        if uaqi_info:
            result.append(f"UAQI: {uaqi_info['aqi']} ({uaqi_info['category']})")
        
        # Add dominant pollutant
        dominant_pollutant = local_info['dominantPollutant'].upper()
        result.append(f"Dominant: {dominant_pollutant}")
        
        # Get pollutant concentrations
        result.append("\nPollutants:")
        for pollutant in data.get('pollutants', []):
            conc = pollutant['concentration']
            if pollutant['code'] == dominant_pollutant.lower():
                result.append(f"➤ {pollutant['displayName']}: {conc['value']:.1f} {conc['units']}")
            else:
                result.append(f"  {pollutant['displayName']}: {conc['value']:.1f} {conc['units']}")
            
        return "\n".join(result)
    except Exception as e:
        print(f"AQI Error: {str(e)}", file=sys.stderr)  # Log the error
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

# Create a compact tooltip with current conditions
data['tooltip'] = f"<b>{location['city']}, {location['country_name']}</b>\n"
data['tooltip'] += f"<b>{current['weather'][0]['description'].capitalize()} {temp:.1f}°</b>\n"
data['tooltip'] += f"Feels: {feels_like:.1f}° | Wind: {current['wind_speed']:.1f}m/s | Hum: {current['humidity']}%\n"
data['tooltip'] += "─" * 30 + "\n"  # Separator
data['tooltip'] += f"{aqi}\n"
data['tooltip'] += "─" * 30 + "\n"  # Separator


# Detailed forecast with hourly details for today and tomorrow
for i, day in enumerate(weather['daily'][:5]):  # Process 5 days
    data['tooltip'] += "\n<b>"
    forecast_date = datetime.fromtimestamp(day['dt'])
    
    # Add day label
    if i == 0:
        data['tooltip'] += "Today, "
    elif i == 1:
        data['tooltip'] += "Tomorrow, "
    else:
        data['tooltip'] += forecast_date.strftime('%A, ')  # Full day name
    data['tooltip'] += f"{forecast_date.strftime('%Y-%m-%d')}</b>\n"
    
    # Compact basic info for all days
    weather_emoji = get_weather_emoji(day['weather'][0]['id'])
    data['tooltip'] += f"{weather_emoji} {day['weather'][0]['description'].capitalize()}"
    data['tooltip'] += f" | ⬆️{day['temp']['max']:.1f}° ⬇️{day['temp']['min']:.1f}°"
    
    # Add sunrise/sunset only for first two days
    if i < 2:
        data['tooltip'] += f" | 🌅{datetime.fromtimestamp(day['sunrise']).strftime('%H:%M')}"
        data['tooltip'] += f" 🌇{datetime.fromtimestamp(day['sunset']).strftime('%H:%M')}\n"
    else:
        data['tooltip'] += f" | 💧{int(day.get('pop', 0) * 100)}%\n"  # Precipitation probability for later days
        continue  # Skip hourly details for days after tomorrow

    # Hourly details only for today and tomorrow
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
                chances = format_chances(hour)
                data['tooltip'] += (
                    f"{hour_time.strftime('%H:%M')} {weather_emoji}"
                    f"{format_temp(hour['temp'])} "
                    f"{hour['weather'][0]['description'][:15]}"  # Truncate description
                )
                if chances:
                    data['tooltip'] += f" ({chances})"
                data['tooltip'] += "\n"


print(json.dumps(data))
