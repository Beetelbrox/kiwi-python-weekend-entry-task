"""Logic related to flight search"""

from itertools import product
from typing import Generator, Iterable

from flight_search.constraints import (
    SearchConstraints,
    TripConstraints,
    departs_on_requested_date,
    is_combination_elegible,
    is_flight_elegible,
    is_trip_elegible,
    is_valid_layover,
)
from flight_search.entities import (
    FlightCombination,
    FlightDetails,
    NullFlightCombination,
    Trip,
)

FlightIndex = dict[str, list[FlightDetails]]


def build_flight_index(flights: Iterable[FlightDetails]) -> FlightIndex:
    """
    Builds a dictionary of flights where all flights with the same origin
    are stored under the same key in order to speedup flight retrieval when
    performing the search.
    """
    index = {}
    for flight in flights:
        index.setdefault(flight.origin, []).append(flight)
    return index


def branch_combination(
    cmb: FlightCombination,
    index: FlightIndex,
    constraints: SearchConstraints,
) -> list[FlightCombination]:
    """
    Given a combination, finds all combinations that can be obtained by
    adding a new flight that departs from the airport where the combination
    ends and is within the layover bounds. Used as part of the search.
    """
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
    """
    Given a flight index and a set of constraints, finds all combinations
    that satisfy the constraints.
    This is achieved by finding all paths between the origin & destination airports
    on the multigraph composed by the flights as edges and airports as nodes.
    The search itself is DFS + backtracking, where we traverse the DAG in a DFS fashion,
    prune branches that don't satisfy the constraints as early as possible to reduce
    the search space. DFS is chosen as it's more memory efficient than BFS.
    Although it's not an issue in the examples provided due to the small order (number
    of vertices) in the graph, we've chosen to implement the DFS using a stack instead of
    recursively to avoid issues with Python's tiny call stack depth.
    """

    stack: list[FlightCombination] = [
        FlightCombination(flight)
        for flight in index.get(constraints.origin, [])
        if departs_on_requested_date(flight, constraints)
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
    """
    Given a flight index, finds all trips that satisfy the given
    constraints. The search itself is done by `find_combinations`,
    this function mainly orchstrates the decision between one-way and
    roundtrip and converts the found combination pairs to trips.
    """

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
        for trip in (
            Trip(dep, ret, constraints.required_bags) for dep, ret in trip_legs
        )
        if is_trip_elegible(trip, constraints)
    )


def search_trips(
    flights: Iterable[FlightDetails],
    constraints: TripConstraints,
) -> Generator[FlightCombination, None, None]:
    """
    Given a flight index, finds all trips that satisfy the given
    constraints
    """

    index: FlightIndex = build_flight_index(
        filter(lambda f: is_flight_elegible(f, constraints), flights)
    )
    return _find_trips(index, constraints)
