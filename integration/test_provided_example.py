import os

import pytest

from flight_search.main import load_flight_details, search_flights
from flight_search.search import SearchConstraints


@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))


def test_output(rootdir):
    flights = load_flight_details(os.path.join(rootdir, "static/0_input.csv"))
    output = search_flights(flights, "BTW", "REJ", SearchConstraints(required_bags=1))
    print(output)
