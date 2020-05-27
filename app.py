from copy import copy
import datetime
import time

import billboard
from song import Song


# The first date the Hot 100 chart is available
CHART_NAME = 'hot-100'
START_DATE = datetime.datetime(1958, 8, 4)
END_DATE = datetime.datetime(2020, 5, 23)
ONE_WEEK = datetime.timedelta(days=7)
DATE_FORMAT = '%Y-%m-%d'


def get_billboard_chart_data_for_week_of(date):
    """Returns billboard.ChartData for given week"""
    return billboard.ChartData(CHART_NAME, date=date.strftime(DATE_FORMAT))


def find(item, collection):
    """Finds the first matching existing item, otherwise returns None"""
    iterable = iter(collection)
    while True:
        try:
            existing_item = next(iterable)
            if existing_item == item:
                return existing_item
        except StopIteration:
            return None


def fetch_all_songs():
    """Returns dict of all songs separated by year"""
    all_songs = set()
    date = copy(START_DATE)

    while date <= END_DATE:
        print('Fetching chart for {}...'.format(date.strftime(DATE_FORMAT)))
        chart_data = get_billboard_chart_data_for_week_of(date)

        if date.strftime(DATE_FORMAT) != chart_data.date:
            # Resetting the date to the chart date to avoid any date issues issues
            date = datetime.datetime.strptime(chart_data.date, DATE_FORMAT)

        for chart_entry in chart_data:
            song = Song(title=chart_entry.title, artist=chart_entry.artist)
            if song in all_songs:
                song = find(song, all_songs)
            else:
                all_songs.add(song)
            song.chart_dates.add(copy(date))

        # Sleeping to avoid ire of rate limiters
        time.sleep(1)
        date = date + ONE_WEEK
        print('Fetched.\n'.format(date.strftime(DATE_FORMAT)))

    return all_songs


if __name__ == '__main__':
    # Get list of all songs (by year) that appear in Billboard Hot 100 (no duplicats by year)
    all_songs = fetch_all_songs()
    #   Save them in a database?
    # Get lyrics for those songs
    # Count the number of times the word 'love' appears in the lyrics and title
    # Output CSV number of times 'love' appears for each year
