#!/usr/bin/env python
"""
Waybar module for displaying moon phases and Hindu calendar information using DrikPanchang
"""

import json
import os
import pickle
from datetime import datetime, timedelta
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
            # Use the proper set_city method with geonames_id
            self.calendar.set_city(
                location.get('geonames_id', '1275339'),  # Default to Mumbai's geonames_id
                location.get('city', 'Mumbai')
            )
        except Exception as e:
            print(f"Error setting up city: {e}")
            # Fallback to Mumbai if there's an error
            self.calendar.set_city('1275339', 'Mumbai')

    def get_next_ekadashi(self):
        """Get the next Ekadashi date and name"""
        try:
            today = datetime.now()
            # Look ahead up to 30 days to find next Ekadashi
            for i in range(30):
                future_date = (today + timedelta(days=i)).strftime("%d/%m/%Y")
                date_obj = self.calendar.get_date(future_date)
                panchang = date_obj.get('panchang', {})
                tithi = panchang.get('Tithi', '')
                if 'Ekadashi' in tithi:
                    return {
                        'date': future_date,
                        'name': tithi.split(' ')[0],  # Get Ekadashi name
                        'full_tithi': tithi.split(' upto ')[0]
                    }
            return None
        except Exception as e:
            print(f"Error getting Ekadashi info: {e}")
            return None

    def get_today_info(self):
        try:
            date_obj = self.calendar.today()
            panchang = date_obj.get('panchang', {})
            next_ekadashi = self.get_next_ekadashi()
            
            return {
                'tithi': panchang.get('Tithi', '').split(' upto ')[0],  # Remove "upto" time
                'nakshatra': panchang.get('Nakshatra', '').split(' upto ')[0],
                'yoga': panchang.get('Yoga', '').split(' upto ')[0],
                'event': date_obj.get('event', ''),
                'regional_date': date_obj.get('regional_datestring', ''),
                'next_ekadashi': next_ekadashi
            }
        except Exception as e:
            print(f"Error getting panchang info: {e}")
            return {
                'tithi': '',
                'nakshatra': '',
                'yoga': '',
                'event': '',
                'regional_date': ''
            }

def get_current_moon_phase():
    """Get current moon phase emoji and name for specific location"""
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
    nfm = ephem.next_full_moon(observer.date)
    pfm = ephem.previous_full_moon(observer.date)
    
    lunation = (observer.date - pnm) / (nnm - pnm)
    
    # Calculate days since previous new moon
    days_since_new = (observer.date - pnm)
    days_to_full = (nfm - observer.date) 
    days_from_full = (observer.date - pfm)
    
    # Determine if we're waxing (New->Full) or waning (Full->New)
    is_waxing = days_to_full < days_from_full
    
    # Get illuminated percentage
    phase_percent = moon.phase

    # Convert phase percentage to appropriate emoji and name
    if phase_percent < 6.25:  # 0-6.25%
        return "🌑", "New Moon"
    elif phase_percent > 93.75:  # 93.75-100%
        return "🌕", "Full Moon"
    elif is_waxing:
        if phase_percent < 43.75:  # 6.25-43.75%
            return "🌒", "Waxing Crescent"
        elif phase_percent < 56.25:  # 43.75-56.25%
            return "🌓", "First Quarter"
        else:  # 56.25-93.75%
            return "🌔", "Waxing Gibbous"
    else:  # Waning
        if phase_percent < 43.75:  # 6.25-43.75%
            return "🌘", "Waning Crescent"
        elif phase_percent < 56.25:  # 43.75-56.25%
            return "🌗", "Last Quarter"
        else:  # 56.25-93.75%
            return "🌖", "Waning Gibbous"

def main():
    # Get moon phase info
    next_full, next_new = get_moon_phases()
    current_phase_emoji, current_phase_name = get_current_moon_phase()
    
    # Get DrikPanchang info
    dp_info = DrikPanchangInfo()
    today_info = dp_info.get_today_info()
    
    # Prepare tooltip text
    tooltip = [
        f"🌕 <b>Moon Phases</b>",
        f"Current Phase: {current_phase_emoji} {current_phase_name}",
        f"Next Full Moon: {next_full.strftime('%Y-%m-%d')}",
        f"Next New Moon: {next_new.strftime('%Y-%m-%d')}",
        "",
        f"📅 <b>Hindu Calendar</b>",
        f"Date: {today_info.get('regional_date', '')}",
        f"Tithi: {today_info.get('tithi', '')}",
        f"Nakshatra: {today_info.get('nakshatra', '')}"
    ]
    
    # Add next Ekadashi info
    next_ekadashi = today_info.get('next_ekadashi')
    if next_ekadashi:
        tooltip.extend([
            "",
            f"🌙 <b>Next Ekadashi</b>",
            f"{next_ekadashi['name']}",
            f"Date: {datetime.strptime(next_ekadashi['date'], '%d/%m/%Y').strftime('%Y-%m-%d')}"
        ])

    # Add event if present
    if today_info.get('event'):
        tooltip.extend(["", f"🎯 <b>Today's Event</b>", today_info['event']])
    
    data = {
        "text": f"{current_phase_emoji}",
        "tooltip": "\n".join(tooltip)
    }
    
    print(json.dumps(data))

if __name__ == "__main__":
    main()
