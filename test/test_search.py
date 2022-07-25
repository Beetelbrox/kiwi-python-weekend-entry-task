import datetime as dt
from distutils.command.build import build

from flight_search.entities import FlightCombination, FlightDetails
from flight_search.main import record_to_flight
from flight_search.search import (
    FlightIndex,
    build_flight_index,
    SearchConstraints,
    branch_combination,
    find_combinations,
)
from flight_search.constraints import SearchConstraints


def make_flight(
    origin: str, dest: str, departure: str, arrival: str, flight_no: str = "FAKE"
):
    return record_to_flight(
        {
            "flight_no": flight_no,
            "origin": origin,
            "destination": dest,
            "departure": departure,
            "arrival": arrival,
            "base_price": 0,
            "bag_price": 0,
            "bags_allowed": 0,
        }
    )


default_constraints = SearchConstraints(
    "AAA", "BBB", 0, dt.timedelta(hours=1), dt.timedelta(hours=6)
)


def test_flight_index_groups_flights_correctly() -> None:
    flights = [
        make_flight("AAA", "CCC", "2022-01-01T13:00:00", "2022-01-01T16:00:00"),
        make_flight("AAA", "DDD", "2022-01-01T14:00:00", "2022-01-01T17:00:00"),
        make_flight("BBB", "DDD", "2022-01-01T14:00:00", "2022-01-01T17:00:00"),
    ]
    index = build_flight_index(flights)
    assert len(index) == 2
    assert len(index["AAA"]) == 2
    assert len(index["BBB"]) == 1


class TestCombinationBranching:
    def test_branching_from_a_combination_finds_connecting_flights(self) -> None:
        combination = FlightCombination(
            make_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T11:00:00")
        )
        flights = [
            make_flight("BBB", "CCC", "2022-01-01T13:00:00", "2022-01-01T16:00:00"),
            make_flight("BBB", "DDD", "2022-01-01T14:00:00", "2022-01-01T17:00:00"),
        ]
        combinations = branch_combination(
            combination, build_flight_index(flights), default_constraints
        )
        assert len(combinations) == 2
        second_legs = {comb.last for comb in combinations}
        for flight in flights:
            assert flight in second_legs

    def test_flight_ignored_when_branching_if_not_a_connection(self) -> None:
        combination = FlightCombination(
            make_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T11:00:00")
        )
        flights = [
            make_flight("CCC", "DDD", "2022-01-01T13:00:00", "2022-01-01T16:00:00"),
        ]
        combinations = branch_combination(
            combination, build_flight_index(flights), default_constraints
        )
        assert len(combinations) == 0

    def test_flight_ignored__when_branching_if_layover_is_invalid(self) -> None:
        combination = FlightCombination(
            make_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T11:00:00")
        )
        flights = [
            make_flight("BBB", "CCC", "2022-01-01T11:30:00", "2022-01-01T23:00:00"),
            make_flight("BBB", "DDD", "2022-01-01T23:00:00", "2022-01-01T23:00:00"),
        ]
        combinations = branch_combination(
            combination, build_flight_index(flights), default_constraints
        )
        assert len(combinations) == 0

    def test_flight_ignored_when_branching_if_destination_already_visited(self) -> None:
        combination = FlightCombination(
            make_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T11:00:00")
        )
        flights = [
            make_flight("BBB", "AAA", "2022-01-01T13:00:00", "2022-01-01T16:00:00"),
        ]
        combinations = branch_combination(
            combination, build_flight_index(flights), default_constraints
        )
        assert len(combinations) == 0


class TestFindCombinations:
    def test_can_find_single_flight_combination(self) -> None:
        flights = [
            make_flight("AAA", "BBB", "2022-01-01T13:00:00", "2022-01-01T16:00:00"),
            make_flight("AAA", "CCC", "2022-01-01T13:00:00", "2022-01-01T16:00:00"),
        ]
        combinations = list(
            find_combinations(build_flight_index(flights), default_constraints)
        )
        assert len(combinations) == 1
        assert combinations[0].first == flights[0]

    def test_can_find_multiple_flight_combination(self) -> None:
        flights = [
            make_flight("AAA", "CCC", "2022-01-01T13:00:00", "2022-01-01T11:00:00"),
            make_flight("CCC", "BBB", "2022-01-01T13:00:00", "2022-01-01T16:00:00"),
        ]
        combinations = list(
            find_combinations(build_flight_index(flights), default_constraints)
        )
        assert len(combinations) == 1
        assert combinations[0].first == flights[0]
        assert combinations[0].last == flights[1]
