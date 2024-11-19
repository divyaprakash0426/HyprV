#!/usr/bin/env python
"""
Waybar module for displaying moon phases and Hindu calendar information using DrikPanchang
"""

import json
import os
import pickle
from datetime import datetime
import ephem
from hindu_calendar import HinduCalendar
from pathlib import Path

# Reuse weather cache for location
CACHE_DIR = Path(os.path.expanduser("~/.cache/waybar-weather"))
CACHE_FILE = CACHE_DIR / "weather_cache.pkl"

def get_location():
    """Load location data from weather cache"""
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'rb') as f:
                _, location = pickle.load(f)
                return location
    except Exception:
        # Default to Mumbai if cache read fails
        return {"city": "Mumbai", "latitude": 19.0760, "longitude": 72.8777}

def get_moon_phases():
    """Calculate next full and new moon dates for specific location"""
    location = get_location()
    observer = ephem.Observer()
    observer.lat = str(location['latitude'])
    observer.lon = str(location['longitude'])
    observer.date = ephem.now()
    
    moon = ephem.Moon()
    moon.compute(observer)
    
    # Calculate next full and new moons from the observer's location
    next_full = ephem.next_full_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    return next_full.datetime(), next_new.datetime()

class DrikPanchangInfo:
    def __init__(self):
        location = get_location()
        self.calendar = HinduCalendar(method='marathi')
        try:
            self.calendar.set_location(
                location['latitude'],
                location['longitude'],
                location['city']
            )
        except Exception as e:
            print(f"Error setting up city: {e}")

    def get_today_info(self):
        try:
            date_obj = self.calendar.today()
            return {
                'tithi': date_obj['panchang'].get('Tithi', ''),
                'nakshatra': date_obj['panchang'].get('Nakshatra', ''),
                'yoga': date_obj['panchang'].get('Yoga', ''),
                'event': date_obj.get('event', ''),
                'regional_date': date_obj.get('regional_datestring', '')
            }
        except Exception as e:
            print(f"Error getting panchang info: {e}")
            return {}

def get_current_moon_phase():
    """Get current moon phase emoji for specific location"""
    location = get_location()
    observer = ephem.Observer()
    observer.lat = str(location['latitude'])
    observer.lon = str(location['longitude'])
    observer.date = ephem.now()
    
    moon = ephem.Moon()
    moon.compute(observer)
    
    # Calculate lunation using the observer's location
    nnm = ephem.next_new_moon(observer.date)
    pnm = ephem.previous_new_moon(observer.date)
    
    lunation = (observer.date - pnm) / (nnm - pnm)
    
    # Convert lunation to moon phase emoji
    if lunation < 0.125:
        return "🌑"  # New Moon
    elif lunation < 0.375:
        return "🌒"  # Waxing Crescent
    elif lunation < 0.625:
        return "🌓"  # First Quarter
    elif lunation < 0.875:
        return "🌔"  # Waxing Gibbous
    else:
        return "🌕"  # Full Moon

def main():
    # Get moon phase info
    next_full, next_new = get_moon_phases()
    current_phase = get_current_moon_phase()
    
    # Get DrikPanchang info
    dp_info = DrikPanchangInfo()
    today_info = dp_info.get_today_info()
    
    # Prepare tooltip text
    tooltip = [
        f"🌕 <b>Moon Phases</b>",
        f"Current Phase: {current_phase}",
        f"Next Full Moon: {next_full.strftime('%Y-%m-%d')}",
        f"Next New Moon: {next_new.strftime('%Y-%m-%d')}",
        "",
        f"📅 <b>Hindu Calendar</b>",
        f"Date: {today_info.get('regional_date', '')}",
        f"Tithi: {today_info.get('tithi', '')}",
        f"Nakshatra: {today_info.get('nakshatra', '')}"
    ]
    
    # Add event if present
    if today_info.get('event'):
        tooltip.extend(["", f"🎯 <b>Today's Event</b>", today_info['event']])
    
    data = {
        "text": current_phase,
        "tooltip": "\n".join(tooltip)
    }
    
    print(json.dumps(data))

if __name__ == "__main__":
    main()
