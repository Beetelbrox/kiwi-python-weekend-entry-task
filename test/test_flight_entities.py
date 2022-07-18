import datetime as dt

import pytest

from flight_search.flights import FlightCombination, FlightDetails


class TestFlightCombination:

    flight_extra_args = [dt.datetime(2022, 1, 1), dt.datetime(2022, 1, 2), 0, 0, 0]

    def test_constructor_builds_visited_airports_set_correctly(self):

        flights = [
            FlightDetails("0000", "AAA", "BBB", *self.flight_extra_args),
            FlightDetails("0001", "BBB", "CCC", *self.flight_extra_args),
            FlightDetails("0002", "DDD", "EEE", *self.flight_extra_args),
        ]
        assert FlightCombination(flights).visited_airports == set(
            ["AAA", "BBB", "CCC", "DDD", "EEE"]
        )

    def test_constructor_fails_on_empty_input(self):
        with pytest.raises(ValueError):
            FlightCombination([])

    def test_adding_a_leg_produces_a_new_combination_with_the_new_flight_appended(self):
        combination = FlightCombination(
            [FlightDetails("0000", "AAA", "BBB", *self.flight_extra_args)]
        )
        new_flight = FlightDetails("0001", "BBB", "CCC", *self.flight_extra_args)
        new_combination = combination.add_leg(new_flight)
        assert combination is not new_combination
        assert len(new_combination) == 2
        assert new_combination.last == new_flight

    def test_adding_a_leg_preserves_order(self):
        flights = [
            FlightDetails("0000", "AAA", "BBB", *self.flight_extra_args),
            FlightDetails("0001", "BBB", "CCC", *self.flight_extra_args),
            FlightDetails("0002", "DDD", "EEE", *self.flight_extra_args),
        ]
        new_combination = FlightCombination(flights[:-1]).add_leg(flights[-1])
        assert list(new_combination) == flights

    def test_joining_two_combinations_yields_a_new_combination_with_the_combined_flights_in_the_same_order(
        self,
    ):
        flights = [
            FlightDetails("0000", "AAA", "BBB", *self.flight_extra_args),
            FlightDetails("0001", "BBB", "CCC", *self.flight_extra_args),
            FlightDetails("0002", "DDD", "EEE", *self.flight_extra_args),
            FlightDetails("0003", "EEE", "CCC", *self.flight_extra_args),
        ]
        combination_1 = FlightCombination(flights[:2])
        combination_2 = FlightCombination(flights[2:])
        assert list(combination_1.join(combination_2)) == flights
