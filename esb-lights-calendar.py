#!/usr/bin/python3
#
# Generate a iCal calendar file for the Empire State Building tower lights
# https://www.esbnyc.com/about/tower-lights/calendar/
#
# Copyright (c) 2021 Sandro Tosi <sandro.tosi@gmail.com>
# License: GPLv2
import calendar
import datetime
import json
from collections import defaultdict

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event

ESB_BASEURL = 'https://www.esbnyc.com/about/tower-lights/calendar'
TODAY = datetime.date.today()
# for now let's just select the current month and the next one
MONTHS = [(TODAY.year, TODAY.month), calendar._nextmonth(TODAY.year, TODAY.month)]

ical = Calendar()
ical.add('VERSION', '2.0')
ical.add('URL', 'https://sandrotosi.github.io/esb-lights-calendar/esb.ics')
ical.add('NAME', 'Empire State Building Lights')
ical.add('X-WR-CALNAME', 'Empire State Building Lights')
ical.add('DESCRIPTION', 'Show what light display is shown on the Empire State Building')
ical.add('X-WR-CALDESC', 'Show what light display is shown on the Empire State Building')
ical.add('X-WR-TIMEZONE', 'UTC')
ical.add('REFRESH-INTERVAL;VALUE=DURATION', 'P1H')
ical.add('X-PUBLISHED-TTL', 'PT6H')

for year, month in MONTHS:
    month_text = f"{year}{month:02d}"
    month_colors = defaultdict(list)

    url = f"{ESB_BASEURL}/{month_text}"

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    for custom_colors in soup.find_all(class_='lse'):
        day = int(custom_colors.find(class_='day--day').text)
        color = custom_colors.find(class_='name').text.title()
        # sometimes the description can be empty
        descr = custom_colors.find(class_='field_description')
        if descr:
            descr = descr.text.strip()

        month_colors[day].append({'color': color, 'description': descr})

    # save a cache of the current data, maybe we're gonna use to provide historical events, one day...
    with open(f"data/{month_text}.json", 'w') as f:
        json.dump(month_colors, f, indent=2)

    for calendar_day in calendar.Calendar().itermonthdays(year=year, month=month):
        if calendar_day == 0:
            continue

        # when there's no specific color in the calendar, ESB is showing the "Signature White" light
        data = month_colors.get(calendar_day, [{'color': 'Signature White', 'description': ''}, ])

        # there are days when multiple colors are displayed (at different times)
        for item in data:
            event = Event()
            event.add('summary', f"ESB: {item['color']}")
            event.add('dtstart', datetime.date(year, month, calendar_day))
            event.add('description', item['description'])
            event.add('class', 'PUBLIC')
            event.add('SEQUENCE', 0)
            event.add('STATUS', 'CONFIRMED')
            event.add('transp', 'TRANSPARENT')  # dont mark as busy??
            event.add('url', url)

            ical.add_component(event)

with open('esb.ics', 'wb') as f:
    f.write(ical.to_ical())
