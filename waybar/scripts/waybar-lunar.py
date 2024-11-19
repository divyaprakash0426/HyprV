#!/usr/bin/env python
"""
Waybar module for displaying moon phases and Ekadashi information
"""

import json
from datetime import datetime, timedelta
import ephem

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
    next_full, next_new = get_moon_phases()
    ekadashi = get_ekadashi_info()
    
    data = {
        "text": get_current_moon_phase(),
        "tooltip": (
            f"🌕 <b>Moon Phases</b>\n"
            f"Next Full Moon: {next_full.strftime('%Y-%m-%d')}\n"
            f"Next New Moon: {next_new.strftime('%Y-%m-%d')}\n\n"
            f"🕉️ <b>Ekadashi</b>\n"
            f"Next: {ekadashi['type']}\n"
            f"Date: {ekadashi['next_ekadashi'].strftime('%Y-%m-%d')}\n"
            f"Start: {ekadashi['start_time']}, End: {ekadashi['end_time']}"
        )
    }
    
    print(json.dumps(data))

if __name__ == "__main__":
    main()
