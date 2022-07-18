import datetime as dt
from dataclasses import dataclass
from itertools import product
from typing import Generator, Iterable

from .flights import FlightCombination, FlightDetails


@dataclass
class SearchConstraints:
    required_bags: int = 0
    min_layover: int = 1
    max_layover: int = 6

    def is_valid_flight(self, flight: FlightDetails) -> bool:
        return flight.bags_allowed >= self.required_bags

    def is_valid_layover(self, inbound: FlightDetails, outbound: FlightDetails) -> bool:
        return (
            dt.timedelta(hours=self.min_layover)
            <= outbound.departure - inbound.arrival
            <= dt.timedelta(hours=self.max_layover)
        )

    def is_valid_combination(self, combination: FlightCombination) -> bool:
        return True


class FlightCatalog:
    """Stores & indexes flights by origin to ease retrieval"""

    def __init__(self, flights: Iterable[FlightDetails] | None = None) -> None:
        self._catalog: dict = {}
        for flight in flights or []:
            self.add_flight(flight)

    def add_flight(self, flight: FlightDetails) -> None:
        self._catalog.setdefault(flight.origin, []).append(flight)

    def get_outbound_flights(self, origin: str) -> list[FlightDetails]:
        return self._catalog.get(origin, [])


def find_combinations_for_route(
    catalog: FlightCatalog,
    origin: str,
    dest: str,
    constraints: SearchConstraints,
) -> Generator[FlightCombination, None, None]:

    stack: list[FlightCombination] = [
        FlightCombination([flight]) for flight in catalog.get_outbound_flights(origin)
    ]

    while stack:
        combination: FlightCombination = stack.pop()
        if combination.destination == dest:
            yield combination
        else:
            next_combinations: Generator[FlightCombination, None, None] = (
                combination.add_leg(flight)
                for flight in catalog.get_outbound_flights(combination.destination)
                if flight.destination not in combination.visited_airports
                and constraints.is_valid_layover(combination.last, flight)
            )
            stack.extend(filter(constraints.is_valid_combination, next_combinations))


def find_combinations(
    flights: Iterable[FlightDetails],
    origin: str,
    dest: str,
    constraints: SearchConstraints,
    is_roundtrip: bool = False,
) -> Generator[FlightCombination, None, None]:
    catalog: FlightCatalog = FlightCatalog(filter(constraints.is_valid_flight, flights))
    departing: Iterable[FlightCombination] = find_combinations_for_route(
        catalog, origin, dest, constraints
    )
    if is_roundtrip:
        returning: Iterable[FlightCombination] = find_combinations_for_route(
            catalog, dest, origin, constraints
        )
        return (
            dep.join(ret)
            for dep, ret in product(departing, returning)
            if ret.first.departure > dep.last.arrival
        )
    return departing
