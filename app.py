from copy import copy
import csv
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
DATA_FILE_NAME = 'all_songs.csv'


def parse_date(date_str):
    """Parses date string in standard format"""
    return datetime.datetime.strptime(date_str, DATE_FORMAT)


def format_date(date):
    """Formats date into standard format"""
    return date.strftime(DATE_FORMAT)


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


def get_billboard_chart_data_for_week_of(date):
    """Returns billboard.ChartData for given week"""
    return billboard.ChartData(CHART_NAME, date=format_date(date))


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
        date += ONE_WEEK
        print('Fetched.\n')

    return all_songs


def save_songs_to_data_file(songs):
    """Saves iterable of songs to CSV file"""
    print("Saving songs to data file...")
    with open(DATA_FILE_NAME, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        header_row = ['title', 'artist', 'chart_dates', 'lyrics']
        writer.writerow(header_row)
        for song in songs:
            dates = '|'.join(map(lambda s: s.strftime(DATE_FORMAT), song.chart_dates))
            writer.writerow([song.title, song.artist, dates, song.lyrics])
    print("Finished saving.\n")


def fetch_songs_from_data_file():
    """Fetches and creates songs from a datafile"""
    print('Fetching songs from data file...')
    all_songs = set()
    with open(DATA_FILE_NAME, newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            chart_dates = set(map(lambda date: datetime.datetime.strptime(date, DATE_FORMAT), row['chart_dates'].split('|')))
            song = Song(title=row['title'],
                        artist=row['artist'],
                        chart_dates=chart_dates)
            all_songs.add(song)
    print('Finished fetching.\n')
    return all_songs


if __name__ == '__main__':
    # Get list of all songs (by year) that appear in Billboard Hot 100 (no duplicats by year)
    all_songs = fetch_all_songs()
    #   Save them in a database?
    # Get lyrics for those songs
    if not Path(f'./{DATA_FILE_NAME}').is_file():
        all_songs = fetch_all_songs()
        save_songs_to_data_file(all_songs)
    else:
        all_songs = fetch_songs_from_data_file()
    # Saving song data with lyrics
    # Count the number of times the word 'love' appears in the lyrics and title
    # Output CSV number of times 'love' appears for each year
