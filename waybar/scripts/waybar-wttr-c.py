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
    print(geo_data)
    
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
    print(weather)

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
    now = ephem.now()
    next_full = ephem.next_full_moon(now)
    next_new = ephem.next_new_moon(now)
    return next_full.datetime(), next_new.datetime()

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
tempint = int(weather['current']['feels_like'])
extrachar = ''
if tempint > 0 and tempint < 10:
    extrachar = '+'  # Add plus sign for positive single digits

data['text'] = ' '+get_weather_emoji(weather['current']['weather'][0]['id']) + \
    " "+extrachar+str(round(weather['current']['feels_like']))+"°"

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
