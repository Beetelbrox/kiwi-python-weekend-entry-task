import datetime as dt

import pytest

from flight_search.entities import FlightCombination, FlightDetails


def fake_flight(origin: str, dest: str) -> FlightDetails:
    dep_ts = dt.datetime(2022, 1, 1)
    ret_ts = dt.datetime(2022, 1, 2)
    return FlightDetails("FAKE", origin, dest, dep_ts, ret_ts, 0, 0, 0)


class TestFlightCombination:

    flight_extra_args = [dt.datetime(2022, 1, 1), dt.datetime(2022, 1, 2), 0, 0, 0]

    def test_visited_airports_set_is_built_correctly_with_single_flight(self) -> None:
        combination = FlightCombination(fake_flight("AAA", "BBB"))
        assert len(combination.visited_airports) == 2
        assert "AAA" in combination.visited_airports
        assert "BBB" in combination.visited_airports

    def test_visited_airports_set_is_built_correctly_with_multiple_flight(self):
        combination = FlightCombination(
            fake_flight("AAA", "BBB"),
            fake_flight("BBB", "CCC"),
            fake_flight("CCC", "DDD"),
        )
        assert len(combination.visited_airports) == 4
        assert "AAA" in combination.visited_airports
        assert "BBB" in combination.visited_airports
        assert "CCC" in combination.visited_airports
        assert "DDD" in combination.visited_airports

    def test_constructor_fails_on_empty_input(self):
        with pytest.raises(ValueError):
            FlightCombination()

    def test_adding_a_leg_produces_a_new_combination_with_the_new_flight_appended(self):
        combination = FlightCombination(fake_flight("AAA", "BBB"))
        new_combination = combination + fake_flight("BBB", "CCC")
        assert len(new_combination) == 2
        assert new_combination.first == fake_flight("AAA", "BBB")
        assert new_combination.last == fake_flight("BBB", "CCC")
        assert combination is not new_combination
