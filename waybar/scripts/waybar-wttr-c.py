#!/usr/bin/env python
"""
Waybar weather module script that fetches weather data from wttr.in
Displays current weather with emoji and temperature in the bar
Shows detailed forecast in the tooltip
"""

import json
import requests
import os
from datetime import datetime

# Dictionary mapping wttr.in weather codes to emoji representations
WEATHER_CODES = {
    '113': '☀️ ',
    '116': '⛅',
    '119': '☁️ ',
    '122': '☁️ ',
    '143': '☁️ ',
    '176': '🌧️',
    '179': '🌧️',
    '182': '🌧️',
    '185': '🌧️',
    '200': '⛈️ ',
    '227': '🌨️',
    '230': '🌨️',
    '248': '☁️ ',
    '260': '☁️ ',
    '263': '🌧️',
    '266': '🌧️',
    '281': '🌧️',
    '284': '🌧️',
    '293': '🌧️',
    '296': '🌧️',
    '299': '🌧️',
    '302': '🌧️',
    '305': '🌧️',
    '308': '🌧️',
    '311': '🌧️',
    '314': '🌧️',
    '317': '🌧️',
    '320': '🌨️',
    '323': '🌨️',
    '326': '🌨️',
    '329': '❄️ ',
    '332': '❄️ ',
    '335': '❄️ ',
    '338': '❄️ ',
    '350': '🌧️',
    '353': '🌧️',
    '356': '🌧️',
    '359': '🌧️',
    '362': '🌧️',
    '365': '🌧️',
    '368': '🌧️',
    '371': '❄️',
    '374': '🌨️',
    '377': '🌨️',
    '386': '🌨️',
    '389': '🌨️',
    '392': '🌧️',
    '395': '❄️ '
}

# Initialize data dictionary for waybar output
data = {}

# Fetch weather data from wttr.in for Gurugram in JSON format
# Read city from config file
config_file = os.path.expanduser('~/.config/hypr/hyprv.conf')
city = None
try:
    with open(config_file, 'r') as f:
        for line in f:
            if line.startswith('SET_CITY='):
                city = line.split('=')[1].strip().strip('"')
                break
    if not city:
        print(json.dumps({"text": "❌", "tooltip": "City not set in hyprv.conf"}))
        exit(1)
except FileNotFoundError:
    print(json.dumps({"text": "❌", "tooltip": "hyprv.conf not found"}))
    exit(1)

weather = requests.get(f"https://wttr.in/{city}?format=j1").json()


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

# Handle special formatting for positive single-digit temperatures
tempint = int(weather['current_condition'][0]['FeelsLikeC'])
extrachar = ''
if tempint > 0 and tempint < 10:
    extrachar = '+'  # Add plus sign for positive single digits

# Prepare the main display text for waybar


data['text'] = ' '+WEATHER_CODES[weather['current_condition'][0]['weatherCode']] + \
    " "+extrachar+weather['current_condition'][0]['FeelsLikeC']+"°"

# Build detailed tooltip with current conditions and forecast
data['tooltip'] = f"<b>{weather['current_condition'][0]['weatherDesc'][0]['value']} {weather['current_condition'][0]['temp_C']}°</b>\n"
data['tooltip'] += f"Feels like: {weather['current_condition'][0]['FeelsLikeC']}°\n"
data['tooltip'] += f"Wind: {weather['current_condition'][0]['windspeedKmph']}Km/h\n"
data['tooltip'] += f"Humidity: {weather['current_condition'][0]['humidity']}%\n"
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
