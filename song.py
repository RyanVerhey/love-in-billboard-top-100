class Song:
    """Represents a song on the billboard Top 100
    Has an artist (required), title (required), lyrics (optional),
    and chart_dates, a set of all dates song appeared on the charts
    """
    def __init__(self, title, artist, lyrics=None, chart_dates=set()):
        self._title = title
        self._artist = artist
        self.lyrics = lyrics
        self.chart_dates = chart_dates

    @property
    def title(self):
        return self._title

    @property
    def artist(self):
        return self._artist

    def __hash__(self):
        return hash((self._title, self._artist))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__hash__() == other.__hash__()
