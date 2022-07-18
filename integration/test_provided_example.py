from flight_search.main import search_flights, load_flight_details
from flight_search.search import SearchConstraints
import pytest
import os

@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))

def test_output(rootdir):
    flights = load_flight_details(os.path.join(rootdir, "static/0_input.csv"))
    output = search_flights(
        flights, "BTW", "REJ", SearchConstraints(required_bags=1))
    print(output)