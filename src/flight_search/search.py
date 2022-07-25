from itertools import product
from typing import Generator, Iterable

from flight_search.constraints import (
    SearchConstraints,
    TripConstraints,
    is_combination_elegible,
    is_flight_elegible,
    is_trip_elegible,
    is_valid_layover,
)
from flight_search.entities import (
    FlightCombination,
    FlightDetails,
    Trip,
    NullFlightCombination,
)

FlightIndex = dict[str, list[FlightDetails]]


def build_flight_index(flights: Iterable[FlightDetails]) -> FlightIndex:
    index = {}
    for flight in flights:
        index.setdefault(flight.origin, []).append(flight)
    return index


def branch_combination(
    cmb: FlightCombination,
    index: FlightIndex,
    constraints: SearchConstraints,
) -> list[FlightCombination]:
    return [
        cmb + flight
        for flight in index.get(cmb.destination, [])
        if flight.destination not in cmb.visited_airports
        and is_valid_layover(cmb.last, flight, constraints)
    ]


def find_combinations(
    index: FlightIndex,
    constraints: SearchConstraints,
) -> Generator[FlightCombination, None, None]:

    stack: list[FlightCombination] = [
        FlightCombination(flight) for flight in index.get(constraints.origin, [])
    ]

    while stack:
        if (cur := stack.pop()).destination == constraints.destination:
            yield cur
        else:
            stack.extend(
                cmb
                for cmb in branch_combination(cur, index, constraints)
                if is_combination_elegible(cmb, constraints)
            )


def _find_trips(
    index: FlightIndex, constraints: TripConstraints
) -> Generator[Trip, None, None]:

    if constraints.returning:
        trip_legs = (
            (dep, ret)
            for dep, ret in product(
                find_combinations(index, constraints.departing),
                find_combinations(index, constraints.returning),
            )
            if ret.first.departure > dep.last.arrival
        )
    else:
        trip_legs = (
            (dep, NullFlightCombination())
            for dep in find_combinations(index, constraints.departing)
        )
    return (
        trip
        for trip in (Trip(dep, ret, constraints.required_bags) for dep, ret in trip_legs)
        if is_trip_elegible(trip, constraints)
    )


def search_trips(
    flights: Iterable[FlightDetails],
    constraints: TripConstraints,
) -> Generator[FlightCombination, None, None]:

    index: FlightIndex = build_flight_index(
        filter(lambda f: is_flight_elegible(f, constraints), flights)
    )
    return _find_trips(index, constraints)
