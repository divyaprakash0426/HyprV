#!/usr/bin/env python
"""
Waybar weather module script that fetches weather data from OpenWeatherMap
Displays current weather with emoji and temperature in the bar
Shows detailed forecast in the tooltip
"""

import json
import requests
import os
from datetime import datetime, timedelta
import ephem  # for moon phases

# Dictionary mapping OpenWeatherMap codes to emoji representations
WEATHER_CODES = {
    # Thunderstorm
    "2": "⛈️",
    # Drizzle
    "3": "🌧️",
    # Rain
    "5": "🌧️",
    # Snow
    "6": "❄️",
    # Atmosphere (fog, mist, etc)
    "7": "🌫️",
    # Clear
    "800": "☀️",
    # Clouds
    "801": "⛅",
    "802": "☁️",
    "803": "☁️",
    "804": "☁️"
}

# Initialize data dictionary for waybar output
data = {}

# Read config file for API key and city
config_file = os.path.expanduser('~/.config/HyprV/hyprv.conf')
city = None
api_key = None

try:
    with open(config_file, 'r') as f:
        for line in f:
            if line.startswith('SET_CITY='):
                city = line.split('=')[1].strip().strip('"')
            elif line.startswith('OPENWEATHERMAP_API_KEY='):
                api_key = line.split('=')[1].strip().strip('"')
    
    if not city or not api_key:
        print(json.dumps({"text": "❌", "tooltip": "City or API key not set in hyprv.conf"}))
        exit(0)
except FileNotFoundError:
    print(json.dumps({"text": "❌", "tooltip": "hyprv.conf not found"}))
    exit(0)

# Fetch current weather and forecast from OpenWeatherMap
try:
    # Get coordinates for the city
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
    geo_response = requests.get(geo_url)
    geo_response.raise_for_status()  # Raise exception for bad status codes
    geo_data = geo_response.json()
    
    if not geo_data:
        print(json.dumps({"text": "❌", "tooltip": "City not found"}))
        exit(0)
        
    lat = geo_data[0]['lat']
    lon = geo_data[0]['lon']
    
    # Get current weather and forecast
    weather_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely&units=metric&appid={api_key}"
    weather_response = requests.get(weather_url)
    weather_response.raise_for_status()
    weather = weather_response.json()

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
        return data['list'][0]['main']['aqi']  # Returns 1-5 scale
    except:
        return "N/A"

def get_moon_phases():
    """Calculate next full and new moon dates"""
    def next_phase(date, phase):
        calc_date = ephem.next_phase(date, phase)
        return calc_date.datetime()

    now = datetime.now()
    next_full = next_phase(now, 0)  # 0 represents full moon
    next_new = next_phase(now, 0.25)  # 0.25 represents new moon
    return next_full, next_new

def get_ekadashi_info():
    """Calculate next Ekadashi dates and times"""
    # Simplified placeholder implementation
    return {
        'next_ekadashi': datetime.now() + timedelta(days=11),
        'type': 'Utpanna Ekadashi',
        'start_time': '05:32',
        'end_time': '09:47'
    }

# Prepare the main display text for waybar
current = weather['current']
temp = current['temp']
feels_like = current['feels_like']
weather_id = current['weather'][0]['id']

# Handle special formatting for positive single-digit temperatures
tempint = int(weather['current_condition'][0]['FeelsLikeC'])
extrachar = ''
if tempint > 0 and tempint < 10:
    extrachar = '+'  # Add plus sign for positive single digits

# Prepare the main display text for waybar


data['text'] = ' '+WEATHER_CODES[weather['current_condition'][0]['weatherCode']] + \
    " "+extrachar+weather['current_condition'][0]['FeelsLikeC']+"°"

# Build detailed tooltip with current conditions and forecast
aqi = get_aqi(lat, lon)
next_full, next_new = get_moon_phases()
ekadashi = get_ekadashi_info()

data['tooltip'] = f"<b>{city}</b>\n"
data['tooltip'] += f"<b>{current['weather'][0]['description'].capitalize()} {temp:.1f}°</b>\n"
data['tooltip'] += f"Feels like: {feels_like:.1f}°\n"
data['tooltip'] += f"Wind: {current['wind_speed']:.1f} m/s\n"
data['tooltip'] += f"Humidity: {current['humidity']}%\n"
data['tooltip'] += f"AQI: {aqi}/5\n\n"

# Add moon and Ekadashi section
data['tooltip'] += "🌕 <b>Moon Phases</b>\n"
data['tooltip'] += f"Next Full Moon: {next_full.strftime('%Y-%m-%d')}\n"
data['tooltip'] += f"Next New Moon: {next_new.strftime('%Y-%m-%d')}\n\n"

data['tooltip'] += "🕉️ <b>Ekadashi</b>\n"
data['tooltip'] += f"Next: {ekadashi['type']}\n"
data['tooltip'] += f"Date: {ekadashi['next_ekadashi'].strftime('%Y-%m-%d')}\n"
data['tooltip'] += f"Start: {ekadashi['start_time']}, End: {ekadashi['end_time']}\n\n"

# Daily forecast
for i, day in enumerate(weather['daily'][:3]):
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

# Hourly forecast for next 24 hours
current_hour = datetime.now().hour
for hour in weather['hourly'][:24]:
    hour_time = datetime.fromtimestamp(hour['dt'])
    if hour_time.hour < current_hour - 2:
        continue
        
    weather_emoji = get_weather_emoji(hour['weather'][0]['id'])
    data['tooltip'] += (
        f"{hour_time.strftime('%H:%M')} {weather_emoji} "
        f"{format_temp(hour['temp'])} "
        f"{hour['weather'][0]['description'].capitalize()}, "
        f"{format_chances(hour)}\n"
    )


print(json.dumps(data))
