#!/usr/bin/env python
"""
Waybar module for displaying moon phases and Hindu calendar information using DrikPanchang
"""

import json
import os
from datetime import datetime
import ephem
from hindu_calendar import HinduCalendar

CONFIG_DIR = os.path.expanduser("~/.config/waybar/scripts")
CONFIG_FILE = os.path.join(CONFIG_DIR, "drikpanchang_config.json")

def get_moon_phases():
    """Calculate next full and new moon dates"""
    now = ephem.now()
    next_full = ephem.next_full_moon(now)
    next_new = ephem.next_new_moon(now)
    return next_full.datetime(), next_new.datetime()

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        "method": "marathi",
        "city": "Mumbai",
        "city_id": "1275339",
        "regional_language": False
    }

class DrikPanchangInfo:
    def __init__(self):
        config = load_config()
        self.calendar = HinduCalendar(
            method=config['method'],
            regional_language=config['regional_language']
        )
        try:
            self.calendar.set_city(config['city_id'], config['city'])
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
    """Get current moon phase emoji"""
    date = ephem.Date(datetime.now())
    nnm = ephem.next_new_moon(date)
    pnm = ephem.previous_new_moon(date)
    
    lunation = (date - pnm) / (nnm - pnm)
    
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
