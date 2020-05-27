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


if __name__ == '__main__':
    pass
    # Get list of all songs (by year) that appear in Billboard Hot 100 (no duplicats by year)
    #   Save them in a database?
    # Get lyrics for those songs
    # Count the number of times the word 'love' appears in the lyrics and title
    # Output CSV number of times 'love' appears for each year
