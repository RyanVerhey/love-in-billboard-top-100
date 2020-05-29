import re

class Song:
    """Represents a song on the billboard Top 100
    Has an artist (required), title (required), lyrics (optional),
    and chart_dates, a set of all dates song appeared on the charts
    """
    def __init__(self, title, artist, lyrics=None, chart_dates=None):
        self._title = title
        self._artist = artist
        self.lyrics = lyrics
        self.chart_dates = chart_dates or set()

    @property
    def title(self):
        return self._title

    @property
    def artist(self):
        return self._artist

    def occurs_in_title_or_lyrics(self, pattern):
        """Takes a regex pattern and returns whether or not that pattern appears
        in the title or lyrics"""
        lyrics = self.lyrics or ''
        matcher = re.compile(pattern, re.I)
        title_match = bool(matcher.search(self._title))
        lyric_match = bool(matcher.search(lyrics))
        return title_match or lyric_match

    def __hash__(self):
        return hash((self._title, self._artist))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__hash__() == other.__hash__()
