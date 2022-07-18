import datetime as dt

from flight_search.flights import FlightDetails
from flight_search.search import (
    FlightCatalog,
    SearchConstraints,
    find_combinations_for_route,
)


def gen_flight(
    origin: str, dest: str, departure: str, arrival: str, flight_no: str = "FAKE"
):
    return FlightDetails.from_record(
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


# def test_index_correctly_groups_flight_by_origin():
#     extra_args = [dt.datetime(2022, 1, 1), dt.datetime(2022, 1, 2), 0, 0, 0]
#     flights = [
#         FlightDetails("0000", "AAA", "BBB", *extra_args),
#         FlightDetails("0001", "AAA", "BBB", *extra_args),
#         FlightDetails("0002", "BBB", "DDD", *extra_args),
#         FlightDetails("0003", "CCC", "BBB", *extra_args),
#     ]
#     index = build_flight_index(flights)
#     for key, vals in index.items():
#         for val in vals:
#             assert key == val.origin
#     assert len(index["AAA"]) == 2
#     assert len(index["BBB"]) == 1
#     assert len(index["CCC"]) == 1


class TestFindCombinations:
    def find_combinations(self, flights, origin, dest, constraints=None):
        combinations = find_combinations_for_route(
            FlightCatalog(flights), origin, dest, constraints or SearchConstraints()
        )
        return list(combinations)

    def test_search_can_find_route_with_single_flight(self) -> None:
        flights = [
            gen_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T12:00:00"),
        ]
        assert list(self.find_combinations(flights, "AAA", "BBB")[0]) == flights

    def test_search_can_find_route_with_single_stop(self):
        flights = [
            gen_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T12:00:00"),
            gen_flight("BBB", "CCC", "2022-01-01T13:00:00", "2022-01-01T14:00:00"),
        ]
        assert list(self.find_combinations(flights, "AAA", "CCC")[0]) == flights

    def test_search_can_find_route_with_multiple_stops(self):
        flights = [
            gen_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T12:00:00"),
            gen_flight("BBB", "CCC", "2022-01-01T13:00:00", "2022-01-01T14:00:00"),
            gen_flight("CCC", "DDD", "2022-01-01T15:00:00", "2022-01-01T16:00:00"),
        ]
        assert list(self.find_combinations(flights, "AAA", "DDD")[0]) == flights

    def test_search_returns_nothing_if_route_doesnt_exist(self):
        flights = [
            gen_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T12:00:00"),
            gen_flight("CCC", "DDD", "2022-01-01T13:00:00", "2022-01-01T14:00:00"),
        ]
        assert not self.find_combinations(flights, "AAA", "DDD")

    def test_search_returns_nothing_if_layover_is_invalid(self):
        flights = [
            gen_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T12:00:00"),
            gen_flight("BBB", "CCC", "2022-01-01T13:00:00", "2022-01-01T14:00:00"),
        ]
        assert not self.find_combinations(
            flights, "AAA", "CCC", SearchConstraints(min_layover=2)
        )


class TestSearchConstraints:
    # Test corner cases of the contraints mostly for doc purposes
    def test_connection_is_valid_if_layover_is_within_range(self) -> None:
        assert SearchConstraints(min_layover=2, max_layover=4).is_valid_layover(
            gen_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T12:00:00"),
            gen_flight("BBB", "CCC", "2022-01-01T15:00:00", "2022-01-01T18:00:00"),
        )

    def test_connection_is_invalid_if_layover_is_below_minimum(self) -> None:
        assert not SearchConstraints(min_layover=2).is_valid_layover(
            gen_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T12:00:00"),
            gen_flight("BBB", "CCC", "2022-01-01T13:00:00", "2022-01-01T14:00:00"),
        )

    def test_connection_is_invalid_if_layover_is_above_minimum(self) -> None:
        assert not SearchConstraints(max_layover=2).is_valid_layover(
            gen_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T12:00:00"),
            gen_flight("BBB", "CCC", "2022-01-01T15:00:00", "2022-01-01T16:00:00"),
        )

    def test_connection_is_valid_if_layover_is_exactly_minimum(self) -> None:
        assert SearchConstraints(min_layover=2).is_valid_layover(
            gen_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T12:00:00"),
            gen_flight("BBB", "CCC", "2022-01-01T14:00:00", "2022-01-01T16:00:00"),
        )

    def test_connection_is_valid_if_layover_is_exactly_maximum(self) -> None:
        assert SearchConstraints(max_layover=2).is_valid_layover(
            gen_flight("AAA", "BBB", "2022-01-01T10:00:00", "2022-01-01T12:00:00"),
            gen_flight("BBB", "CCC", "2022-01-01T14:00:00", "2022-01-01T14:00:00"),
        )
