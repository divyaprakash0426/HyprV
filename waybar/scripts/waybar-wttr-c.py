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
    geo_data = requests.get(geo_url).json()
    
    if not geo_data:
        print(json.dumps({"text": "❌", "tooltip": "City not found"}))
        exit(0)
        
    lat = geo_data[0]['lat']
    lon = geo_data[0]['lon']
    
    # Get current weather and forecast
    weather_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely&units=metric&appid={api_key}"
    weather = requests.get(weather_url).json()
except requests.RequestException as e:
    print(json.dumps({"text": "❌", "tooltip": f"Weather API error: {str(e)}"}))
    exit(0)


def format_time(time):
    """Format hour time by removing trailing zeros and ensuring 2 digits"""
    return time.replace("00", "").zfill(2)


def format_temp(temp):
    """Format temperature with degree symbol and left padding"""
    return (hour['FeelsLikeC']+"°").ljust(3)


def format_chances(hour):
    """Calculate and format probability of various weather conditions"""
    chances = {
        "chanceoffog": "Fog",
        "chanceoffrost": "Frost",
        "chanceofovercast": "Overcast",
        "chanceofrain": "Rain",
        "chanceofsnow": "Snow",
        "chanceofsunshine": "Sunshine",
        "chanceofthunder": "Thunder",
        "chanceofwindy": "Wind"
    }

    conditions = []
    for event in chances.keys():
        if int(hour[event]) > 0:
            conditions.append(chances[event]+" "+hour[event]+"%")
    return ", ".join(conditions)

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

# Handle special formatting for positive single-digit temperatures
tempint = int(weather['current_condition'][0]['FeelsLikeC'])
extrachar = ''
if tempint > 0 and tempint < 10:
    extrachar = '+'  # Add plus sign for positive single digits

# Prepare the main display text for waybar


data['text'] = ' '+WEATHER_CODES[weather['current_condition'][0]['weatherCode']] + \
    " "+extrachar+weather['current_condition'][0]['FeelsLikeC']+"°"

# Build detailed tooltip with current conditions and forecast
# Get additional data
aqi = get_aqi(weather['nearest_area'][0]['latitude'], weather['nearest_area'][0]['longitude'])
next_full, next_half = get_moon_phases()
ekadashi = get_ekadashi_info()

data['tooltip'] = f"<b>{city}</b>\n"
data['tooltip'] += f"<b>{weather['current_condition'][0]['weatherDesc'][0]['value']} {weather['current_condition'][0]['temp_C']}°</b>\n"
data['tooltip'] += f"Feels like: {weather['current_condition'][0]['FeelsLikeC']}°\n"
data['tooltip'] += f"Wind: {weather['current_condition'][0]['windspeedKmph']}Km/h\n"
data['tooltip'] += f"Humidity: {weather['current_condition'][0]['humidity']}%\n"
data['tooltip'] += f"AQI: {aqi}/5\n\n"

# Add moon and Ekadashi section
data['tooltip'] += "🌕 <b>Moon Phases</b>\n"
data['tooltip'] += f"Next Full Moon: {next_full.strftime('%Y-%m-%d')}\n"
data['tooltip'] += f"Next New Moon: {next_half.strftime('%Y-%m-%d')}\n\n"

data['tooltip'] += "🕉️ <b>Ekadashi</b>\n"
data['tooltip'] += f"Next: {ekadashi['type']}\n"
data['tooltip'] += f"Date: {ekadashi['next_ekadashi'].strftime('%Y-%m-%d')}\n"
data['tooltip'] += f"Start: {ekadashi['start_time']}, End: {ekadashi['end_time']}\n\n"
for i, day in enumerate(weather['weather']):
    data['tooltip'] += "\n<b>"
    if i == 0:
        data['tooltip'] += "Today, "
    if i == 1:
        data['tooltip'] += "Tomorrow, "
    data['tooltip'] += f"{day['date']}</b>\n"
    data['tooltip'] += f"⬆️ {day['maxtempC']}° ⬇️ {day['mintempC']}° "
    data['tooltip'] += f"🌅 {day['astronomy'][0]['sunrise']} 🌇 {day['astronomy'][0]['sunset']}\n"
    for hour in day['hourly']:
        if i == 0:
            if int(format_time(hour['time'])) < datetime.now().hour-2:
                continue
        data['tooltip'] += f"{format_time(hour['time'])} {WEATHER_CODES[hour['weatherCode']]} {format_temp(hour['FeelsLikeC'])} {hour['weatherDesc'][0]['value']}, {format_chances(hour)}\n"


print(json.dumps(data))
