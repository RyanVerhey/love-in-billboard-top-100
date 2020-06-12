from contextlib import contextmanager
from collections import OrderedDict
from copy import copy
import csv
import datetime
from functools import reduce
import json
import os
from pathlib import Path
import sys
import time

import billboard
import lyricsgenius
from song import Song


CHART_NAME = 'hot-100'
# The first date the Hot 100 chart is available
START_DATE = datetime.datetime(1958, 8, 4)
# When I started writing script
END_DATE = datetime.datetime(2020, 5, 23)
ONE_WEEK = datetime.timedelta(days=7)
DATE_FORMAT = '%Y-%m-%d'
DATA_FILE_NAME = 'all_songs.csv'
csv.field_size_limit(sys.maxsize)


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


@contextmanager
def suppress_print():
    """Suppresses calls to `print` inside the block"""
    sys.stdout = open(os.devnull, 'w')
    yield
    sys.stdout = sys.__stdout__


def get_billboard_chart_data_for_week_of(date):
    """Returns billboard.ChartData for given week"""
    return billboard.ChartData(CHART_NAME, date=format_date(date))


def build_songs_from_billboard_data(chart_data):
    """Turns songs from Billboard chart data into Song objects"""
    date = parse_date(chart_data.date)
    songs = set()
    for chart_entry in chart_data:
        songs.add(
            Song(title=chart_entry.title,
                 artist=chart_entry.artist,
                 chart_dates=set([date])))

    return songs


def fetch_all_songs():
    """Returns set of all fetched songs"""
    all_songs = set()
    date = copy(START_DATE)

    while date <= END_DATE:
        print('Fetching chart for {}...'.format(format_date(date)))
        chart_data = get_billboard_chart_data_for_week_of(date)
        date = parse_date(chart_data.date)
        songs = build_songs_from_billboard_data(chart_data)

        for song in songs:
            if song in all_songs:
                existing_song = find(song, all_songs)
                existing_song.chart_dates.update(song.chart_dates)
            else:
                all_songs.add(song)

        # Sleeping to avoid ire of rate limiters
        time.sleep(10)
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
            dates = '|'.join(map(lambda s: format_date(s), song.chart_dates))
            writer.writerow([song.title, song.artist, dates, song.lyrics])
    print("Finished saving.\n")


def fetch_songs_from_data_file():
    """Fetches and creates songs from a datafile"""
    print('Fetching songs from data file...')
    all_songs = set()
    with open(DATA_FILE_NAME, newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            chart_dates = set(map(lambda date: parse_date(date), row['chart_dates'].split('|')))
            song = Song(title=row['title'],
                        artist=row['artist'],
                        chart_dates=chart_dates,
                        lyrics=row['lyrics'])
            all_songs.add(song)
    print('Finished fetching.\n')
    return all_songs


def save_missing_info(song=None, artist=None):
    """Takes a song and missing info ('title' or 'artist') and saves that to a JSON file"""
    try:
        with open('missing_info.json', 'r') as jsonfile:
            file_data = jsonfile.read()
    except FileNotFoundError:
        file_data = ''

    if file_data:
        json_data = json.loads(file_data)
    else:
        json_data = {'artists': [], 'songs': []}

    if artist and not song:
        json_data['artists'].append(artist)
    elif song and artist:
        json_data['songs'].append({'title': song, 'artist': artist})

    with open('missing_info.json', 'w') as jsonfile:
        jsonfile.write(json.dumps(json_data))


def fetch_lyrics_for_songs(all_songs):
    """Fetches lyrics for all supplied songs"""
    all_songs = copy(all_songs)
    print("Finding lyrics...")
    genius = lyricsgenius.Genius(os.environ['GENIUS_ACCESS_TOKEN'])
    def reduce_by_artist(artist_dict, song):
        if song.artist not in artist_dict.keys():
            artist_dict[song.artist] = set()
        artist_dict[song.artist].add(song)
        return artist_dict
    songs_by_artist = reduce(reduce_by_artist, all_songs, dict())
    for artist_name, songs in songs_by_artist.items():
        try:
            with suppress_print():
                genius_artist = genius.search_artist(artist_name, max_songs=1)
        except Exception as e:
            print(f'Failed at artist {artist_name}')
            raise e
        if not genius_artist:
            print(f'Artist not found: {artist_name}')
            save_missing_info(artist=artist_name)
            continue
        for song in songs:
            with suppress_print():
                genius_song = genius.search_song(song.title, genius_artist.name)
            if not genius_song:
                print(f'Song not found: {song.title} by {artist_name}')
                save_missing_info(song=song.title, artist=artist_name)
                continue
            song.lyrics = genius_song.lyrics
            # Sleeping to avoid ire of rate limiters
            time.sleep(10)

    print("All available lyrics found.")
    return all_songs


def find_occurrences_of_pattern_by_year(songs, pattern):
    def organize_by_year(year_dict, song):
        years = set(map(lambda d: d.year, song.chart_dates))
        for year in years:
            if year not in year_dict.keys():
                year_dict[year] = 0
            if song.occurs_in_title_or_lyrics(pattern):
                year_dict[year] += 1
        return year_dict
    return reduce(organize_by_year, songs, dict())


def save_pattern_occurrence_data_to_data_file(occurrences_by_year):
    ordered_occurrences_by_year = OrderedDict(occurrences_by_year.items())
    with open('results.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)
        header_row = ['year', 'occurrences']
        writer.writerow(header_row)
        for year, num_of_occurrences in ordered_occurrences_by_year.items():
            writer.writerow((year, num_of_occurrences))


if __name__ == '__main__':
    if not Path(f'./{DATA_FILE_NAME}').is_file():
        all_songs = fetch_all_songs()
        save_songs_to_data_file(all_songs)
    else:
        all_songs = fetch_songs_from_data_file()
    if not any(map(lambda song: song.lyrics, all_songs)):
        pass
        # only getting lyric info if not already available
        all_songs = fetch_lyrics_for_songs(all_songs)
        # Saving songs with lyrics to data file
        save_songs_to_data_file(all_songs)
    # Count the number of times the word 'love' appears in the lyrics and title
    love_by_year = find_occurrences_of_pattern_by_year(all_songs, r'love')
    # Output CSV number of times 'love' appears for each year
    save_pattern_occurrence_data_to_data_file(love_by_year)

