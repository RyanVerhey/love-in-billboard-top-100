from contextlib import contextmanager
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
                        chart_dates=chart_dates)
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

    print("All available lyrics found.")
    return all_songs


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
        # save_songs_to_data_file(all_songs)
    # Saving song data with lyrics
    # Count the number of times the word 'love' appears in the lyrics and title
    # Output CSV number of times 'love' appears for each year
